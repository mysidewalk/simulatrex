FROM jupyter/minimal-notebook:python-3.11

# fix-permissions ensures directories are writable by users in the root and single user group
# the simplest way to do this (though it is probable overkill) is to fix permissions at the beginning and end
USER root
RUN fix-permissions /opt

# Copy less volatile files
COPY docker/environment.yml /opt/simulatrex/docker/environment.yml
# Update environment with mamba, cleanup after
RUN mamba update --all -y && \
    mamba env update --file /opt/simulatrex/docker/environment.yml && \
    mamba clean --all -yf

# Copy more volatile files
COPY . /opt/simulatrex/
# Fix permissions of copied files
RUN fix-permissions /opt/simulatrex
# Install simulatrex in local/editable mode, uninstall a bad dependency, and purge pip cache
RUN pip install -e /opt/simulatrex && \
    pip uninstall -y py && \
    pip cache purge
