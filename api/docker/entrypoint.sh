#!/bin/sh
set -e -x

# We add the postgres UUID extension
export PGPASSWORD=${POSTGRES_PASSWORD}
export POSTGRES_USER=postgres
psql -U ${POSTGRES_USER} -h postgres -w -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' ${POSTGRES_USER}

# we copy the frontend files, if any so we can serve them from the outside
if [ -d "frontend" ]; then
    mkdir -p /frontend
    cp -r frontend/* /frontend/
    export REEL2BITS_SPA_HTML=/frontend/index.html
fi
exec "$@"