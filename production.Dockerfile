FROM python:3.11-slim as python-base
ENV PYTHONUNBUFFERED=1 \
  POETRY_HOME="/opt/poetry" \
  POETRY_VIRTUALENVS_IN_PROJECT=True \
  POETRY_NO_INTERACTION=1 \
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv"

ENV PATH="${POETRY_HOME}/bin:${VENV_PATH}/bin:$PATH"

FROM python-base as builder-base
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  curl build-essential

# install poetry
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN poetry install --no-dev


FROM python-base as production
ENV FASTAPI_ENV=production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY ./ /app/
WORKDIR /app

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "api:app"]
