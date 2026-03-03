FROM codercom/code-server:4.109.5

USER root

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER 1000
