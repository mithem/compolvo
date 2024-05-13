FROM debian:12

RUN mkdir -p /home/compolvo
WORKDIR /home/compolvo

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv neovim curl
RUN python3 -m venv venv
COPY . .
RUN bash -c "source venv/bin/activate && pip3 install -r src/agent/requirements.txt"


ENTRYPOINT ["sleep", "10000"]