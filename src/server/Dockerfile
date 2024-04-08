FROM python:3.11

RUN mkdir -p /usr/local/compolvo
WORKDIR /usr/local/compolvo

# Copy requirements before rest so entire python environment still is cached by Docker when files other than requirements.txt change
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT sleep 5 && python3 server.py