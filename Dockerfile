FROM alpine:3.23.0

RUN apk add --no-cache jq
RUN apk add --no-cache \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/main \
    postgresql18-client
