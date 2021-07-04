FROM python:2
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y python3-dev
RUN apt-get install -y libssl-dev libffi-dev
RUN apt-get install -y swig
RUN apt-get install openssl && apt-get install ca-certificates
RUN pip install m2crypto
# RUN apt-get install -y python-suds
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir /cfdi
WORKDIR /cfdi
COPY requirements.txt /cfdi/
RUN pip install -r requirements.txt
COPY . /cfdi/
