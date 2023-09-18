FROM python:3.11
ENV PYTHONUNBUFFERED True

COPY requirements.txt /
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /
WORKDIR /
