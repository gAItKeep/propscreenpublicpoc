FROM python:3.9-slim-buster

RUN apt update && apt install -y --no-install-recommends --no-install-suggests libpq-dev python3-dev python3-virtualenv gcc

RUN python3 -m venv venv
RUN . venv/bin/activate

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip install --upgrade virtualenv

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN pip install awscli

COPY . .


CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]