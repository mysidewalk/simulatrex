"""
Author: Dominik Scherm (dom@simulatrex.ai)

File: models.py
Description: LLM Models

"""
import os
import json
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from pydantic import BaseModel
import openai
import requests
import instructor

load_dotenv()

from simulatrex.agent_utils.types import CognitiveModel
from simulatrex.utils.log import SingletonLogger

_logger = SingletonLogger

DEFAULT_SYSTEM_PROMPT = "This is a real-world like simulation. Try to answer the following questions as best as possible:"


class BaseLanguageModel(ABC):
    @abstractmethod
    async def ask(
        self, prompt: str, context_prompt=DEFAULT_SYSTEM_PROMPT, temperature=0.9
    ) -> str:
        pass

    @abstractmethod
    async def generate_structured_output(
        self,
        prompt: str,
        response_model: BaseModel,
        context_prompt=DEFAULT_SYSTEM_PROMPT,
        temperature=0.9,
    ) -> dict:
        pass


class OpenAILanguageModel(BaseLanguageModel):
    """
    This is a wrapper for the OpenAI API.
    """

    def __init__(self, model_id=CognitiveModel.GPT_4, agent_id=None):
        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key is None:
            raise Exception(
                "No OpenAI API key found. Please set OPENAI_API_KEY as environment variable."
            )

        self.api_key = api_key
        self.model_id = model_id
        self.agent_id = agent_id

        # Patch the openai.ChatCompletion.create and openai.ChatCompletion.acreate methods to support the response_model parameter.
        instructor.patch()

    async def ask(
        self, prompt: str, context_prompt=DEFAULT_SYSTEM_PROMPT, temperature=0.9
    ) -> str:
        try:
            chat_completion = openai.ChatCompletion.create(
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=self.model_id.value,
                max_retries=2,
                temperature=temperature,
            )
            response_message = chat_completion["choices"][0].message.content

            # Log the response
            if self.agent_id:
                _logger.log_agent_response(self.agent_id, response_message)

            return response_message
        except Exception as e:
            _logger.debug(f"Error: {e}")

            raise Exception("Error in OpenAI API call")

    async def generate_structured_output(
        self,
        prompt: str,
        response_model: BaseModel,
        context_prompt=DEFAULT_SYSTEM_PROMPT,
        temperature=0.9,
    ):
        try:
            structured_response = openai.ChatCompletion.create(
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_model=response_model,
                model=self.model_id.value,
                max_retries=2,
                temperature=temperature,
            )

            # Log the response
            if self.agent_id:
                # Convert the structured response to a readable string
                response_string = json.dumps(structured_response, indent=4, default=str)
                _logger.log_agent_response(self.agent_id, response_string)

            return structured_response
        except Exception as e:
            _logger.debug(f"Error: {e}")

            raise Exception("Error in OpenAI API call")


class LlamaLanguageModel(BaseLanguageModel):
    """
    This class is a wrapper for the LLama API.
    """

    def __init__(self, model_id=CognitiveModel.LLAMA_2_70b, agent_id=None):
        access_token = os.environ.get("HUGGINGFACE_ACCESS_TOKEN")

        if access_token is None:
            raise Exception(
                "No Huggingface API key found. Please set HUGGINGFACE_API_KEY as environment variable."
            )

        self.access_token = access_token
        self.model_id = model_id
        self.agent_id = agent_id

    async def ask(self, prompt: str) -> str:
        if self.model_id == CognitiveModel.LLAMA_2_70b:
            try:
                API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
                headers = {"Authorization": f"Bearer {self.access_token}"}

                response = requests.post(
                    API_URL,
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "options": {
                            "use_cache": False,
                            "wait_for_model": True,
                        },
                        "parameters": {
                            "max_length": 4096,
                        },
                    },
                )

                result = response.json()
                result_text = result["generated_text"]

                # Log the response
                if self.agent_id:
                    _logger.log_agent_response(self.agent_id, result_text)

                return result_text
            except Exception as e:
                _logger.debug(f"Error: {e}")

                raise Exception("Error in HuggingFace API call")
