FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /bin/

ARG UID=1000
ARG GID=1000
ARG USER=donna

RUN groupadd --gid $GID $USER && useradd --create-home --uid $UID --gid $USER --shell /bin/bash $USER

USER $USER

WORKDIR /repository

CMD []
