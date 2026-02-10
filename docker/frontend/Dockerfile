# Build Stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend_repo/package.json frontend_repo/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend_repo/ .

# Inject config.js script tag into all HTML files in pages/
# We do this before build so the copied HTML files include it.
# We insert it before the closing </head> tag.
RUN find pages -name "*.html" -exec sed -i 's|</head>|<script src="/config.js"></script></head>|' {} +

# Overwrite api.js with our modified version that uses window.APP_CONFIG
# This file will be bundled by esbuild.
COPY docker/frontend/api.js js/api.js

# Build the project (HTML copy, CSS build, JS bundle)
RUN npm run build:prod

# Runtime Stage
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx config
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY docker/frontend/entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
