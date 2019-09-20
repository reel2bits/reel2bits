FROM alpine:3.8

RUN apk add --no-cache git libffi sox taglib libmagic tzdata libmad boost libsndfile libid3tag
RUN apk add --no-cache --virtual .build-deps gcc g++ libffi-dev postgresql-dev
RUN ln -s /usr/bin/python3 /usr/bin/python

COPY ./requirements.txt .

RUN pip3 install --upgrade pip  && \
    pip3 install setuptools wheel && \
    pip3 install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["./docker/server.sh"]

COPY . /app
WORKDIR /app