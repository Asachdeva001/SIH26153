FROM oven/bun:1.0 as builder
WORKDIR /app

COPY frontend/package.json frontend/bun.lockb* ./
RUN bun install

COPY frontend/ .
RUN bun run build

FROM node:20-slim
WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
