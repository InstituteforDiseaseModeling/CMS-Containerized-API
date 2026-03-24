# CMS API Deployment Guide

## Repository Changes

This implementation extends the **cms-containerized** repository provided by IDM. The following modifications were made:

- Renamed the original Dockerfile:
  - `Dockerfile` → `Dockerfile.cms`
  - Azure requires a `Dockerfile` at the repository root, so this preserves the original file.

- Added a new `Dockerfile` for cloud deployment.

- Added validation and API components:
  - `emodl_validator.py` — validates EMODL syntax and reports errors
  - `schemas.py` — defines API input/output structure
  - `api_main.py` — main FastAPI application
  - `simple_cms_wrapper.py` — handles file I/O and executes EMODL → trajectory processing

- Updated dependencies:
  - Added `fastapi`, `uvicorn`, and `pydantic` to `requirements.txt`

- Added tests:
  - Ensures validation functionality works as expected

> **Note:** These changes are visible when copying the repository locally and opening a pull request. Linksbridge does not have write access to the original repository.

---

## Local Deployment

### Prerequisites
- Anaconda installed

### Setup Steps

1. **Unzip the project folder**

2. **Create a virtual environment**

    conda create -n cms anaconda

3. **Activate the environment**

    conda activate cms

4. **Install dependencies**

    cd <path-to-unzipped-folder>  
    pip install --upgrade -r requirements.txt

5. **Run the API**

    python api_main.py

---

### Access the Service

- The API will run at:

    http://127.0.0.1:8000

- Open Swagger UI:

    http://127.0.0.1:8000/docs

---

### Usage

- Select an endpoint in `/docs`
- Modify parameters as needed
- Execute the request

> Processing may take several minutes depending on inputs.

---

## Cloud Deployment (Azure CLI)

This deployment works **as-is** with no additional code changes.

### Prerequisites

- Azure CLI installed  
- Logged into the correct subscription  
- Proper permissions granted  

---

### Initial Deployment

#### 1. Create Resources

**Resource Group**

    az group create \
      --name <your-resource-group-name> \
      --location eastus2

**Azure Container Registry (ACR)**

    az acr create \
      --name <your-acr-name> \
      --resource-group <your-resource-group-name> \
      --sku Basic \
      --admin-enabled true

**Container Apps Environment**

    az containerapp env create \
      --name <your-environment-name> \
      --resource-group <your-resource-group-name> \
      --location eastus2

---

#### 2. Build and Push Image

    az acr build \
      --registry <your-acr-name> \
      --image <your-image-name>:latest .

---

#### 3. Create Container App

    az containerapp create \
      --name <your-app-name> \
      --resource-group <your-resource-group-name> \
      --environment <your-environment-name> \
      --image <your-acr-name>.azurecr.io/cms-api:latest \
      --target-port 3100 \
      --ingress external \
      --min-replicas 0 \
      --max-replicas 2 \
      --cpu 1.0 \
      --memory 2Gi

---

### Updating an Existing App

1. Modify code locally

2. Build and push new image:

    az acr build \
      --registry <your-acr-name> \
      --image <your-image-name>:latest .

3. Update the container app:

    az containerapp update \
      --name <your-app-name> \
      --resource-group <your-resource-group-name> \
      --image <your-acr-name>.azurecr.io/<your-image-name>:latest

---

## Maintenance Tips

- This workflow relies on local deployments and is more fragile than typical CI/CD pipelines
- Strongly recommended:
  - Code reviews
  - Testing before deployment
- Consider assigning a dedicated reviewer/deployer for consistency

---

## Cloud Deployment (Azure Portal)

### Required Resources

- Azure Container Registry (ACR)
- Azure Web App (Containers)

---

## Azure Container Registry Setup

1. Go to: https://portal.azure.com  

2. Create resource:
   - Search **Container Registry**
   - Click **Create**

3. Configure:
   - **Subscription**: Select
   - **Resource Group**: Create or select
   - **Registry Name**: Must be globally unique
   - **Region**: Closest to users
   - **SKU**:
     - Basic (testing)
     - Standard (recommended)
     - Premium (advanced features such as private endpoints and geo-replication)

4. Networking:
   - Public access: Enabled (default)
   - Allow trusted services: Yes

5. Encryption:
   - Default settings are sufficient

6. Review + Create

7. After deployment:
   - Go to resource
   - Copy **Login Server** (e.g. `myregistry.azurecr.io`)

8. Enable:
   - **Admin Credentials** under Access Keys

---

## Azure Web App Setup

### 1. Create Web App

- Go to **App Services → Create**

#### Basics

- Name: `cms-api`
- Publish: Docker Container
- Operating System: Linux
- Region: Closest region
- App Service Plan: **B1 or higher**

#### Docker Tab

- Use a temporary image:

    mcr.microsoft.com/appsvc/staticsite:latest

- Create the app

---

### 2. Configure Deployment

1. Navigate to:

    Web App → Deployment Center

2. Configure:
   - Source: **GitHub Actions**
   - Connect repository

3. Add workflow:
   - Generates a YAML pipeline in your repository

4. Select:
   - Azure Container Registry

5. Set image name:

    idmcontainers/streamlit-demo-app

---

### 3. Continuous Deployment

- GitHub Actions will:
  - Automatically build
  - Automatically deploy
  - Trigger on every push to the configured branch

---

## Summary

This project provides:

- A FastAPI-based CMS API
- Local development via Anaconda
- Cloud deployment via:
  - Azure CLI (Container Apps)
  - Azure Portal (Web Apps + GitHub Actions)