FROM python:3.12

RUN mkdir -p /usr/local/compolvo
WORKDIR /usr/local/compolvo

COPY server.py .
COPY compolvo .

ENTRYPOINT python3 server.py