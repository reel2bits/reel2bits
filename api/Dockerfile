FROM genesix/docker-audiowaveform-alpine:latest as audiowaveform-builder

FROM alpine:3.9

RUN apk add --no-cache sox sox-dev taglib libmagic file-dev libffi libffi-dev postgresql-client python3-dev libxml2 py3-lxml bash ffmpeg libmediainfo boost boost-program_options libsndfile libid3tag gd libmad
RUN apk add --no-cache --virtual .build-deps cmake gcc g++ make pkgconfig git boost-dev gd-dev libmad-dev libsndfile-dev libid3tag-dev wget postgresql-dev libxml2-dev taglib-dev

COPY ./requirements.txt .

RUN pip3 install --upgrade pip  && \
    pip3 install setuptools wheel && \
    pip3 install --no-cache-dir -r /requirements.txt && \
    pip3 install sentry-sdk

COPY --from=audiowaveform-builder /bin/audiowaveform /usr/local/bin

RUN apk del .build-deps

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["./docker/server.sh"]

COPY . /app
WORKDIR /app