#!/usr/bin/bash
export DOLLAR="$"
envsubst < /etc/nginx/template.conf > /etc/nginx/nginx.conf && nginx -g 'daemon off;'; sleep 1000