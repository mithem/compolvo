FROM nginx:latest
WORKDIR /etc/nginx

COPY ssl-terminal.template.conf template.conf
COPY reverse-proxy-entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/reverse-proxy-entrypoint.sh

ENTRYPOINT ["reverse-proxy-entrypoint.sh"]