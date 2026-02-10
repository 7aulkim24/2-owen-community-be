# Deployment Guide

This guide explains how to deploy the Community Service application using Docker for local testing and Bash scripts for AWS EC2 deployment.

## Architecture

- **Frontend:** Static HTML/JS served by Nginx.
  - Features dynamic runtime configuration (`config.js`) to point to the backend.
  - Uses custom Nginx configuration to handle SPA-like routing (extensionless URLs).
- **Backend:** FastAPI application with MySQL database.
  - Configurable CORS via environment variables.

## Local Development & Simulation (Docker Compose)

To simulate the production environment locally using Docker:

1.  **Clone the Frontend Repository:**
    Currently, the Docker setup expects the frontend code in `frontend_repo/`.
    ```bash
    git clone https://github.com/7aulkim24/2-owen-community-fe.git frontend_repo
    ```

2.  **Start the Stack:**
    ```bash
    docker compose up --build
    ```
    This will start:
    - **Frontend:** http://localhost:3000
    - **Backend API:** http://localhost:8000
    - **Database:** MySQL 8.0 on port 3306

3.  **Verify:**
    - Open http://localhost:3000 in your browser.
    - It should load the login page and be able to communicate with the backend.

## AWS EC2 Deployment (Big Bang)

The deployment uses two EC2 instances: one for the Frontend and one for the Backend (which includes the Database).

### 1. Backend Deployment

1.  **Launch an EC2 Instance:**
    - OS: Ubuntu 22.04 LTS (or 24.04).
    - Security Group: Allow inbound traffic on ports **22 (SSH)** and **8000 (API)**.

2.  **Prepare User Data Script:**
    - Open `scripts/deploy-backend.sh`.
    - Update `REPO_URL` with your backend repository URL (e.g., this repository).
      - If it is a private repository, use a Personal Access Token in the URL: `https://<TOKEN>@github.com/<USER>/<REPO>.git`.

3.  **Execute Deployment:**
    - Paste the content of `scripts/deploy-backend.sh` into the **User Data** field when launching the instance.
    - OR, SSH into the instance and run the script manually:
      ```bash
      sudo ./deploy-backend.sh
      ```

4.  **Verify Backend:**
    - Wait for initialization (check `/var/log/cloud-init-output.log`).
    - Access `http://<BACKEND_PUBLIC_IP>:8000/docs` to see Swagger UI.

### 2. Frontend Deployment

1.  **Launch an EC2 Instance:**
    - OS: Ubuntu 22.04 LTS.
    - Security Group: Allow inbound traffic on ports **22 (SSH)** and **80 (HTTP)**.

2.  **Prepare User Data Script:**
    - Open `scripts/deploy-frontend.sh`.
    - **Crucial:** Update `BACKEND_API_URL` with the **Public IP** or Domain of your deployed Backend instance.
      - Example: `BACKEND_API_URL="http://54.123.45.67:8000"`

3.  **Execute Deployment:**
    - Paste the content of `scripts/deploy-frontend.sh` into the **User Data** field.
    - The script will automatically configure Nginx to serve the app and handle routing.

4.  **Verify Frontend:**
    - Access `http://<FRONTEND_PUBLIC_IP>`.
    - You should see the login page.

### 3. Connect Frontend & Backend (CORS)

By default, the Backend only allows requests from `localhost`. You must allow the Frontend EC2 to communicate with it.

1.  **SSH into the Backend EC2 Instance.**
2.  **Edit the Environment File:**
    ```bash
    sudo nano /home/ubuntu/backend/.env
    ```
3.  **Update `ALLOWED_ORIGINS`:**
    Add your Frontend Public URL to the list.
    ```env
    ALLOWED_ORIGINS=["http://localhost:3000", "http://<FRONTEND_PUBLIC_IP>"]
    ```
    *(Note: Ensure it is a valid JSON list of strings)*
4.  **Restart the Backend Service:**
    ```bash
    sudo systemctl restart fastapi_app
    ```
5.  **Final Test:**
    - Go to your Frontend URL in the browser.
    - Try to Login or Sign Up.
    - It should work without CORS errors.

## Troubleshooting

- **CORS Errors:** Check the browser console. If you see "Access-Control-Allow-Origin", verify step 3 above.
- **Backend Connection Refused:** Ensure Security Group for Backend allows port 8000 from the internet (or specifically from Frontend IP).
- **Frontend 404 on Refresh:** The Nginx config should handle this (`try_files`), but verify `/etc/nginx/sites-available/default` on Frontend EC2.
