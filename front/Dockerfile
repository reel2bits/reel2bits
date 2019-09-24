FROM node:11

# needed to compile translations
RUN curl -L -o /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && chmod +x /usr/local/bin/jq

# Bring in gettext so we can get `envsubst`
RUN apt update && apt install -y gettext 

EXPOSE 8081
WORKDIR /app/
ADD package.json yarn.lock ./
RUN yarn install

COPY . .

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["yarn", "dev"]