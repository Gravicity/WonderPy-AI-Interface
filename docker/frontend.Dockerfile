# Multi-stage build for WonderPy AI-Interface Frontend

FROM node:20-alpine as base

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Development mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production build stage
FROM base as build
RUN npm run build

# Production stage
FROM nginx:alpine as production
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx-frontend.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
