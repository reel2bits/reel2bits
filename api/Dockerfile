FROM genesix/docker-audiowaveform-alpine:latest as audiowaveform-builder

FROM alpine:3.13

RUN apk add --no-cache sox sox-dev taglib libmagic file-dev libffi libffi-dev postgresql-client python3-dev libxml2 py3-lxml bash ffmpeg libmediainfo boost boost-program_options libsndfile libid3tag gd libmad rust
RUN apk add --no-cache --virtual .build-deps cmake gcc g++ make pkgconfig git boost-dev gd-dev libmad-dev libsndfile-dev libid3tag-dev wget postgresql-dev libxml2-dev taglib-dev

COPY ./requirements.txt .

RUN pip install --upgrade pip  && \
    pip install setuptools wheel && \
    pip install --no-cache-dir -r /requirements.txt && \
    pip install sentry-sdk

COPY --from=audiowaveform-builder /bin/audiowaveform /usr/local/bin

RUN apk del .build-deps

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["./docker/server.sh"]

COPY . /app
WORKDIR /app
