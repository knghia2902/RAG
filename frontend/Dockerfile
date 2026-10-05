FROM node:22.19.0-bookworm-slim@sha256:4a4884e8a44826194dff92ba316264f392056cbe243dcc9fd3551e71cea02b90 AS web
WORKDIR /app/frontend
ENV NEXT_TELEMETRY_DISABLED=1
COPY package*.json ./
RUN npm ci
COPY . .
ARG API_TARGET=http://backend:8000
ENV API_TARGET=$API_TARGET
RUN npm run build
RUN chown -R node:node /app/frontend/.next
USER node
CMD ["npm", "run", "start"]

FROM mcr.microsoft.com/playwright:v1.63.0-noble@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27 AS browser
WORKDIR /app/frontend
ENV NEXT_TELEMETRY_DISABLED=1
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "test:e2e"]
