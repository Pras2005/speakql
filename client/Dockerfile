# Frontend image
FROM node:18-slim

WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# Copy the frontend code
COPY . /app

# Build the React app
RUN pnpm run build

# Expose the Vite port
EXPOSE 5173

# Start the app
CMD ["pnpm", "run", "dev"]

