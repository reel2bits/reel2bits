#!/bin/sh
set -e
#

if [ -z "$APP_DB_URI" ]; then
    # the official postgres image uses 'postgres' as default user if not set explicitly.
    if [ -z "$POSTGRES_ENV_POSTGRES_USER" ]; then
        export POSTGRES_ENV_POSTGRES_USER=postgres
    fi
    export APP_DB_URI=postgres://$POSTGRES_ENV_POSTGRES_USER:$POSTGRES_ENV_POSTGRES_PASSWORD@postgres:5432/$POSTGRES_ENV_POSTGRES_USER
fi

# We add the postgres UUID extension
psql -U ${POSTGRES_ENV_POSTGRES_USER} -p${POSTGRES_ENV_POSTGRES_PASSWORD} -h postgres -w -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' ${POSTGRES_ENV_POSTGRES_USER}

# we copy the frontend files, if any so we can serve them from the outside
if [ -d "frontend" ]; then
    mkdir -p /frontend
    cp -r frontend/* /frontend/
    export REEL2BITS_SPA_HTML=/frontend/index.html
fi
exec "$@"