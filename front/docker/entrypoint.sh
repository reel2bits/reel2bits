#!/bin/sh
set -e

if [ -z "$REEL2BITS_HOSTNAME_PREFIX" ]; then
    # sed the file with REEL2BITS_HOSTNAME
    VUE_PROXY_HOST=$REEL2BITS_HOSTNAME_PREFIX
else
    export VUE_PROXY_HOST="${REEL2BITS_HOSTNAME_PREFIX}.${REEL2BITS_HOSTNAME_SUFFIX}"
fi

envsubst "`env | awk -F = '{printf \" $$%s\", $$1}'`" \
  < /app/config/local.json.template \
  > /app/config/local.json

cat /app/config/local.json

exec "$@"