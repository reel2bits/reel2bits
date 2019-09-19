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
RUN apk add --no-cache --virtual .build-deps \
    cmake gcc g++ make pkgconfig git boost-dev gd-dev libmad-dev libsndfile-dev libid3tag-dev libffi-dev
RUN apk add --no-cache git libffi sox taglib libmagic tzdata libmad boost libsndfile libid3tag postgresql-dev wget
RUN pip install --no-cache-dir -r requirements.txt

# Build audiowaveform
RUN git clone https://github.com/bbcrd/audiowaveform.git /tmp/audiowaveform && cd /tmp/audiowaveform && \
    wget https://github.com/google/googletest/archive/release-1.8.0.tar.gz -O gmock-1.8.0.tar.gz && tar xzf gmock-1.8.0.tar.gz && \
    ln -s googletest-release-1.8.0/googletest googletest && ln -s googletest-release-1.8.0/googlemock googlemock && \
    mkdir build && cd build && cmake .. && make && cp audiowaveform /app/ && cd .. && rm -rf audiowaveform && \
    apk del .build-deps

ADD . /app/
ADD entrypoint.sh /
ADD config.py.sample /config/config.py

VOLUME ["/data", "/config"]

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["celery", "worker", "-A", "tasks.celery", "--loglevel=error"]
