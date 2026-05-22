# syntax=docker/dockerfile:1.7
# DataScope AI Frontend — Next.js 16 with standalone output
# Image size target: ~250 MB

# ---------- Stage 1: Base ----------
# Shared base for both deps and builder stages
FROM node:22-alpine AS base

# pnpm via corepack (built into recent Node images)
RUN corepack enable && corepack prepare pnpm@10.33.2 --activate

# Alpine doesn't include libc compatibility for some native modules.
# sharp (image optimization) needs this. So does Next's SWC compiler.
RUN apk add --no-cache libc6-compat

WORKDIR /app

# ---------- Stage 2: Dependencies ----------
# Install all deps including devDependencies (needed for build).
# Separated from builder stage so this layer caches when only code changes.
FROM base AS deps

COPY package.json pnpm-lock.yaml ./

# --frozen-lockfile: fail if pnpm-lock.yaml is out of sync (CI safety)
# --prefer-offline: use local store when possible (faster CI builds)
RUN pnpm install --frozen-lockfile --prefer-offline

# ---------- Stage 3: Builder ----------
# Compiles Next.js into .next/standalone/
FROM base AS builder

# Build-time env vars. These bake into the bundle for NEXT_PUBLIC_* values.
# Provide via --build-arg at docker build time.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Disable Next.js telemetry in CI/Docker (privacy + noise reduction)
ENV NEXT_TELEMETRY_DISABLED=1

# Reuse the deps layer
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build it. With output: 'standalone' in next.config.ts, this produces:
#   .next/standalone/  -> trimmed runtime (server.js + minimal node_modules)
#   .next/static/      -> static assets (CSS, JS chunks, fonts)
#   public/            -> user-provided static files
RUN pnpm build

# ---------- Stage 4: Runtime ----------
# Minimal image with only what's needed to run the standalone server.
FROM node:22-alpine AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Non-root user (Alpine uses a different syntax than Debian)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

# Remove bundled npm/npx/corepack (they ship with node:22-alpine but are
# unused by the standalone Next.js server). Eliminates HIGH CVEs in npm's
# bundled deps (e.g. picomatch via tinyglobby) and shrinks the image.
RUN rm -rf /usr/local/lib/node_modules/npm \
           /usr/local/bin/npm \
           /usr/local/bin/npx \
           /usr/local/lib/node_modules/corepack \
           /usr/local/bin/corepack

# Standalone bundle: trimmed runtime with only used packages
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Static assets and public files (not included in standalone bundle)
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

# Simple healthcheck: hit the homepage, expect 200
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# server.js is what `output: 'standalone'` generates
CMD ["node", "server.js"]
