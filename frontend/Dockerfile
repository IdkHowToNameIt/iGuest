# Frontend image: Vite dev server. The source is mounted as a volume in
# docker-compose (with node_modules kept in the image), so edits hot-reload.
FROM node:20-alpine

WORKDIR /app

# Install dependencies first for layer caching. `npm ci` for reproducible installs
# from the committed lock file (which includes the optional cross-platform binaries).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host 0.0.0.0 makes the dev server reachable from outside the container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
