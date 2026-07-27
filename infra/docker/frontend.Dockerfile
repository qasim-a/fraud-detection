FROM node:22-alpine

WORKDIR /app
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml /app/
RUN pnpm install --frozen-lockfile
COPY frontend /app

EXPOSE 5173
CMD ["pnpm", "run", "dev"]
