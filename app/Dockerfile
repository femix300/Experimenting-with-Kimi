FROM node:20-alpine AS build

WORKDIR /app

# Build arg for the backend URL
ARG VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .

# Pass the API URL to Vite at build time
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config for SPA routing + API proxy
RUN echo 'server { \
    listen 8080; \
    root /usr/share/nginx/html; \
    index index.html; \
    location = /index.html { \
        add_header Cache-Control "no-store, no-cache, must-revalidate"; \
        try_files $uri =404; \
    } \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
