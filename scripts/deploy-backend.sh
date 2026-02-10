#!/bin/bash
set -e

# --- Configuration ---
REPO_URL="YOUR_BACKEND_REPO_URL" # Replace with your Backend Repository URL
REPO_DIR="/home/ubuntu/backend"
DB_PASSWORD="owensm1p"
DB_NAME="community"

# --- Install Dependencies ---
echo "Updating system and installing dependencies..."
apt-get update
# python3-venv, python3-pip, python3-dev, libmysqlclient-dev, gcc, pkg-config are needed
apt-get install -y python3-pip python3-venv python3-dev libmysqlclient-dev gcc pkg-config git mysql-server

# --- Setup MySQL ---
echo "Setting up MySQL..."
systemctl start mysql
systemctl enable mysql

# Set root password and create database
# Note: In some MySQL versions on Ubuntu, root uses auth_socket by default.
# We change it to use password authentication.
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';" || mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -u root -p"$DB_PASSWORD" -e "FLUSH PRIVILEGES;"
mysql -u root -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"

# --- Clone Repository ---
echo "Cloning backend repository..."
# Ideally, you would use an SSH key or a public repo.
# For private repos, consider using a Personal Access Token in the URL: https://TOKEN@github.com/...
if [ -d "$REPO_DIR" ]; then
    rm -rf "$REPO_DIR"
fi
git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR"

# --- Initialize Database Schema ---
echo "Initializing database schema..."
mysql -u root -p"$DB_PASSWORD" "$DB_NAME" < db/schema.sql

# --- Setup Python Environment ---
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install .
pip install gunicorn uvloop httptools # Production server dependencies

# Create upload directories
mkdir -p public/image/post public/image/profile
chown -R ubuntu:ubuntu public

# --- Create .env file ---
# You can customize this or rely on defaults in config.py
echo "Creating .env file..."
cat <<EOF > .env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=false
# IMPORTANT: Update this with your Frontend EC2 Public IP or Domain
# Example: ALLOWED_ORIGINS=["http://localhost:3000", "http://54.123.45.67"]
ALLOWED_ORIGINS=["http://localhost:3000", "http://YOUR_FRONTEND_IP"]
EOF

# --- Setup Systemd Service ---
echo "Setting up Systemd service..."
cat <<EOF > /etc/systemd/system/fastapi_app.service
[Unit]
Description=FastAPI Application
After=network.target mysql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$REPO_DIR
Environment="PATH=$REPO_DIR/venv/bin:/usr/bin"
EnvironmentFile=$REPO_DIR/.env
ExecStart=$REPO_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
EOF

# Start Service
systemctl daemon-reload
systemctl enable fastapi_app
systemctl start fastapi_app

echo "Backend deployment complete!"
