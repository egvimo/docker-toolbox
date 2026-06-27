FROM ubuntu:26.04

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends 7zip 7zip-rar unrar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
