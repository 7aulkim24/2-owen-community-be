#!/bin/sh

# Set default API URL if not provided
API_URL=${API_BASE_URL:-http://localhost:8000}

echo "Generating config.js with API_BASE_URL=$API_URL"

# Create config.js in the web root
cat <<EOF > /usr/share/nginx/html/config.js
window.APP_CONFIG = {
    API_BASE_URL: "$API_URL"
};
EOF

# Exec the CMD (nginx)
exec "$@"
