# Spielpendium Operations and Deployment Guide

This guide details the procedures for deploying **Spielpendium** to production environments, setting up containerization
using Docker, and managing database operations.

---

## 1. Production Deployment Architectures

For development, Dash runs using Werkzeug's single-threaded server. In a production environment, you must use a
production WSGI/ASGI server behind a reverse proxy for reliability and performance.

```mermaid
graph LR
    User["User Browser"] -->|HTTPS (Port 443)| Nginx["Nginx Reverse Proxy"]
    Nginx -->|Proxy Pass (Port 8000)| Gunicorn["Gunicorn (WSGI Server)"]
    Gunicorn -->|Run| Dash["Spielpendium App"]
```

### WSGI Server Configuration (Gunicorn)

Install `gunicorn` inside your production python environment:

```bash
pip install gunicorn
```

To run Spielpendium with Gunicorn, bind it to port `8000` and define the entry point (`app:server`):

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 app:server
```

> [!TIP]
> **Worker Counts**
> The recommended number of Gunicorn workers is `2 * number_of_cores + 1`. For a 2-core cloud VM, use 5 workers.

### Reverse Proxy (Nginx)

Configure Nginx as a reverse proxy in `/etc/nginx/sites-available/spielpendium`:

```nginx
server {
    listen 80;
    server_name spielpendium.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optimizing Static Asset Delivery
    location /assets/ {
        alias /path/to/spielpendium/assets/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

---

## 2. Dockerization

Spielpendium includes standard containerization files to build and deploy effortlessly on Docker, Kubernetes, or
container platforms (e.g. Google Cloud Run).

### `Dockerfile`

A standard production-ready `Dockerfile`:

```dockerfile
# Use a lightweight official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Start app with Gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:server"]
```

### `docker-compose.yml`

For deploying the app and persisting its database locally:

```yaml
version: '3.8'

services:
  spielpendium:
    build: .
    ports:
      - "8080:8000"
    volumes:
      - spielpendium_data:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/collection.db
    restart: always

volumes:
  spielpendium_data:
```

---

## 3. Database Administration & Backups

Spielpendium uses a single, robust SQLite database file powered by SQLModel/SQLAlchemy. SQLite is incredibly fast,
simple, and self-contained, which makes backups effortless.

### Finding Your Database File

By default, the database is stored at:

- **Development**: `/Users/eddie/python_projects/spielpendium/db/spielpendium.db` (or relative path in project folder)
- **Docker Volume**: `/app/data/collection.db`

### Backing Up the Database

Because SQLite is a single file, you can create a safe, consistent snapshot by performing a backup command.

**Using the SQLite CLI (Recommended)**:
This command performs an online backup without locking the database or disrupting users:

```bash
sqlite3 db/spielpendium.db ".backup 'db/spielpendium_backup_$(date +%F).db'"
```

**Simple Copy (Only when app is idle)**:

```bash
cp db/spielpendium.db db/spielpendium_backup.db
```

### Restoring the Database

To restore a backup, stop the application, rename the active database, and replace it with the backup:

```bash
mv db/spielpendium.db db/spielpendium_corrupted.db
cp db/spielpendium_backup.db db/spielpendium.db
```

### Database Migration Policy

- The database schema is managed automatically by SQLModel.
- On startup, the system calls `create_db_and_tables()` to safely add new tables or missing columns without deleting
  existing data.
