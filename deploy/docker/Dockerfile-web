# vim:set ft=dockerfile:
FROM python:3.6-alpine

LABEL maintainer="Dashie <dashie@sigpipe.me>"

LABEL org.label-schema.license=AGPL3 \
    org.label-schema.name=reel2bits-web \
    org.label-schema.vcs-url=https://dev.sigpipe.me/dashie/reel2bits \
    org.label-schema.build-date=$DRONE_BUILD_STARTED \
    org.label-schema.vcs-ref=$DRONE_COMMIT_SHA

RUN mkdir -p /app /data /config
WORKDIR /app

ADD requirements.txt /app/
RUN apk add --no-cache git libffi sox taglib libmagic tzdata libmad boost libsndfile libid3tag
RUN apk add --no-cache --virtual .build-deps gcc g++ libffi-dev postgresql-dev
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .build-deps

ADD . /app/
ADD entrypoint.sh /
ADD config.py.sample /config/config.py

VOLUME ["/data", "/config"]

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["flask", "run"]
