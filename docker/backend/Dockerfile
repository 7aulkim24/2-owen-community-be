FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# gcc, pkg-config are needed for some python packages to compile
# default-libmysqlclient-dev is needed if using mysqlclient (though aiomysql is pure python, better safe)
# netcat-openbsd is for wait-for-it.sh
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
# We copy explicitly to avoid copying unwanted files (like .git, .env, etc.)
COPY pyproject.toml .
COPY README.md .
COPY config.py .
COPY main.py .
COPY controllers/ controllers/
COPY db/ db/
COPY models/ models/
COPY routers/ routers/
COPY schemas/ schemas/
COPY test/ test/
COPY utils/ utils/

# Install dependencies
RUN pip install --no-cache-dir .

# Create directory for uploads
RUN mkdir -p public/image/post public/image/profile

# Copy wait-for-it script
COPY docker/backend/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
