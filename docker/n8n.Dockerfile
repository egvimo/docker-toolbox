FROM node:22-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

FROM base AS build
WORKDIR /build
RUN apk add --no-cache git
RUN git clone https://github.com/egvimo/n8n-nodes-apprise.git .
RUN pnpm install --frozen-lockfile
RUN pnpm run build

FROM n8nio/n8n:2.4.5

COPY --from=build --chown=node:node /build/dist /usr/local/lib/node_modules/n8n-nodes-apprise/

ENV N8N_CUSTOM_EXTENSIONS="/usr/local/lib/node_modules/n8n-nodes-apprise"
