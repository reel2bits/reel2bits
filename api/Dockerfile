FROM alpine:3.8

RUN apk add --no-cache sox sox-dev taglib libmagic file-dev libffi libffi-dev postgresql-client python3-dev libxml2 py3-lxml bash ffmpeg libmediainfo boost libsndfile libid3tag gd libmad
RUN apk add --no-cache --virtual .build-deps cmake gcc g++ make pkgconfig git boost-dev gd-dev libmad-dev libsndfile-dev libid3tag-dev wget postgresql-dev libxml2-dev taglib-dev

COPY ./requirements.txt .

RUN pip3 install --upgrade pip  && \
    pip3 install setuptools wheel && \
    pip3 install --no-cache-dir -r /requirements.txt

RUN git clone https://github.com/bbcrd/audiowaveform.git /tmp/audiowaveform && cd /tmp/audiowaveform && \
    wget https://github.com/google/googletest/archive/release-1.8.0.tar.gz -O gmock-1.8.0.tar.gz && tar xzf gmock-1.8.0.tar.gz && \
    ln -s googletest-release-1.8.0/googletest googletest && ln -s googletest-release-1.8.0/googlemock googlemock && \
    mkdir build && cd build && cmake .. && make && mkdir -p /usr/local/bin && cp audiowaveform /usr/local/bin/ && cd .. && rm -rf audiowaveform && \
    apk del .build-deps

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["./docker/server.sh"]

COPY . /app
WORKDIR /app