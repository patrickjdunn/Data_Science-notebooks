FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# System tools: psql + R
RUN apt-get update && apt-get install -y \
    postgresql-client \
    r-base \
    r-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Helpful Python libs (optional but common for your labs)
RUN python -m pip install --upgrade pip && \
    pip install -U pandas sqlalchemy psycopg2-binary jupyterlab

# R packages + IRkernel (so R appears in Jupyter)
RUN R -e "install.packages(c('IRkernel','tidyverse','janitor','skimr'), repos='https://cloud.r-project.org')" && \
    R -e "IRkernel::installspec(user = FALSE)"
