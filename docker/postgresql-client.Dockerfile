FROM alpine:3.23.4

# tag-version: postgresql18-client
RUN apk add --no-cache \
    --repository=https://dl-cdn.alpinelinux.org/alpine/edge/main \
    postgresql18-client=18.3-r0
