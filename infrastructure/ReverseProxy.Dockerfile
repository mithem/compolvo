FROM nginx:latest
WORKDIR /etc/nginx

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

COPY reverse-proxy.template.conf template.conf
COPY reverse-proxy-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/reverse-proxy-entrypoint.sh

RUN mkdir -p /usr/share/compolvo/ansible
WORKDIR /usr/share/compolvo
COPY playbooks.conf.yml .
COPY ansible/templates ansible/templates
COPY requirements.txt .
COPY generate_playbooks.py .
RUN python3 -m venv venv
RUN . venv/bin/activate && pip3 install -r requirements.txt
RUN . venv/bin/activate && python3 generate_playbooks.py generate

RUN mkdir -p /var/www/html/compolvo/ansible
RUN cp -r ansible/playbooks /var/www/html/compolvo/ansible/playbooks

ENTRYPOINT ["reverse-proxy-entrypoint.sh"]
