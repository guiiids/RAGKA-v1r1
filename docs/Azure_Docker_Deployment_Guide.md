# Azure App Service Containerized Deployment Guide

This document outlines the checklist of files you’ll need and provides a step-by-step walkthrough to:
1. Containerize your Python project with Docker.
2. Push your image to Docker Hub.
3. Deploy the container to Azure App Service using the Azure CLI.
4. Configure environment variables in Azure.

---

## 1. Files Checklist

- **Dockerfile**  
- **.dockerignore**  
- **requirements.txt** (Python dependencies)  
- **runtime.txt** (Python runtime version, e.g. `python-3.9.12`)  
- **.env** (local environment variables—not committed)  
- **source code** (e.g. `main.py`, `config.py`, `db_manager.py`, etc.)  
- **Procfile** (optional, if you have a custom startup command)  

---

## 2. Docker Setup

### 2.1. Create `Dockerfile`
```dockerfile
FROM python:3.9-slim

# Set working dir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000"]
```

### 2.2. Create `.dockerignore`
```
__pycache__/
*.pyc
.env
*.log
.git
```

---

## 3. Build & Test Locally

```bash
# Build image
docker build -t myapp:latest .

# Run container locally
docker run --env-file .env -p 8000:8000 myapp:latest
```

---

## 4. Push to Docker Hub

1. **Log in**  
   ```bash
   docker login
   ```
2. **Tag**  
   ```bash
   docker tag myapp:latest <DOCKERHUB_USER>/myapp:latest
   ```
3. **Push**  
   ```bash
   docker push <DOCKERHUB_USER>/myapp:latest
   ```

---

## 5. Azure CLI Prerequisites

- Install Azure CLI: https://aka.ms/installazurecliwindows / macOS / Linux  
- Log in to Azure:  
  ```bash
  az login
  ```

---

## 6. Create Azure Resources

```bash
# Set variables
export RG_NAME="rg-sbx-19-switzerlandnorth-usr-capozzol"
export APP_PLAN="ragka-v1_5"
export WEBAPP_NAME="RAGKA-v1_5"
export LOCATION="switzerlandnorth"

# 1. Create resource group
az group create \
  --name $RG_NAME \
  --location $LOCATION

# 2. Create App Service plan (Linux, SKU B1)
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RG_NAME \
  --is-linux \
  --sku B1

# 3. Create Web App for Containers
az webapp create \
  --resource-group $RG_NAME \
  --plan $APP_PLAN \
  --name $WEBAPP_NAME \
  --deployment-container-image-name <DOCKERHUB_USER>/myapp:latest
```

---

## 7. Configure Environment Variables

```bash
# Example: Set connection string & secret
az webapp config appsettings set \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME \
  --settings \
    DB_HOST="your-db-host" \
    DB_USER="user" \
    DB_PASS="password" \
    SECRET_KEY="supersecret"
```

---

## 8. Update Container Settings (Optional)

If you need to change the image or tag later:

```bash
az webapp config container set \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME \
  --docker-custom-image-name <DOCKERHUB_USER>/myapp:stable \
  --docker-registry-server-url https://index.docker.io
```

---

## 9. Verify & Browse

```bash
# Stream logs
az webapp log tail \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME

# Open in browser
az webapp browse \
  --resource-group $RG_NAME \
  --name $WEBAPP_NAME
```

---

## 10. Cleanup (Optional)

```bash
az group delete \
  --name $RG_NAME \
  --yes --no-wait
```

---

_End of guide._
