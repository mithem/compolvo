FROM nginx:latest
WORKDIR /etc/nginx

COPY reverse-proxy.template.conf template.conf
COPY reverse-proxy-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/reverse-proxy-entrypoint.sh

RUN mkdir -p /var/www/html/compolvo
COPY ansible/playbooks /var/www/html/compolvo/ansible/playbooks

ENTRYPOINT ["reverse-proxy-entrypoint.sh"]