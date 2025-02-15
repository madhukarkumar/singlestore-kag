# Use Node.js 18 as the base image
FROM node:18-slim

# Install pnpm
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install

# Copy the rest of the application
COPY . .

# Build the application
RUN pnpm run build

# Expose the port Next.js runs on
EXPOSE 3000

# Start the application
CMD ["pnpm", "start"]
