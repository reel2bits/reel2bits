#!/bin/bash -eux


envsubst "`env | awk -F = '{printf \" $$%s\", $$1}'`" \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/nginx.conf \
  && cat /etc/nginx/nginx.conf \
  && nginx-debug -g 'daemon off;'