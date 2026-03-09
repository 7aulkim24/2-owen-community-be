#!/bin/sh
set -eu

envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
  < /etc/nginx/templates/nginx.community.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
