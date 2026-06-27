FROM alpine:3.24.1

# tag-version: postgresql18-client
RUN apk add --no-cache \
    postgresql18-client=18.4-r0
