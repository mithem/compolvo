FROM debian:12

RUN mkdir -p /home/compolvo
WORKDIR /home/compolvo

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv neovim curl
RUN python3 -m venv venv
RUN bash -c "source venv/bin/activate && pip3 install -r src/agent/requirements.txt -r src/server/requirements.txt"

COPY . .

ENTRYPOINT ["sleep", "10000"]