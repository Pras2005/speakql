# Frontend Dockerfile
FROM node:18-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY client/package.json client/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# Copy frontend source files
COPY ./client /app

# Expose the port Vite runs on
EXPOSE 5173

# Start the frontend app
CMD ["pnpm", "run", "dev"]

