# GCP VM deployment with GitHub Actions

This repo now includes:

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `deploy/docker-compose.prod.yml`
- `deploy/.env.prod.example`

The deployment model is:

1. GitHub Actions builds Docker images for `backend` and `frontend`
2. Images are pushed to GitHub Container Registry (`ghcr.io`)
3. The deploy workflow SSHes into your GCP VM
4. The VM pulls the new images and restarts the stack with Docker Compose

## 1. Create the GCP VM

Example choices:

- OS: Ubuntu 22.04 LTS
- Machine type: `e2-medium` or larger
- Disk: at least 20 GB
- Firewall: allow HTTP (`80`) and SSH (`22`)

If you want direct browser access by IP or domain, open port `80` on the VM firewall.

## 2. Install Docker on the VM

SSH into the VM:

```bash
gcloud compute ssh <VM_NAME> --zone <ZONE>
```

Install Docker and Compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 3. Prepare the application directory on the VM

Choose a deploy directory, for example:

```bash
mkdir -p /opt/marketgrid/deploy
```

Create the production env file:

```bash
cp /opt/marketgrid/deploy/.env.prod.example /opt/marketgrid/.env.prod
```

If the example file is not there yet, create `/opt/marketgrid/.env.prod` manually with these values:

```env
APP_NAME=marketgrid
GHCR_NAMESPACE=your-github-username
BACKEND_IMAGE=ecommerce-backend
FRONTEND_IMAGE=ecommerce-frontend
IMAGE_TAG=latest
POSTGRES_USER=ecuser
POSTGRES_PASSWORD=strong-postgres-password
POSTGRES_DB=ecommerce
MONGO_DB=ecommerce_logs
JWT_SECRET=strong-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
LOW_STOCK_THRESHOLD_DEFAULT=10
CORS_ORIGINS=https://your-domain-or-vm-ip
FRONTEND_PORT=80
```

Important:

- `GHCR_NAMESPACE` must match your GitHub username or org in lowercase.
- `BACKEND_IMAGE` and `FRONTEND_IMAGE` are based on the repository name.
- `CORS_ORIGINS` should be your real public URL or VM IP.

## 4. Create a GitHub token for the VM

The VM needs to pull private images from GHCR unless your package visibility is public.

Create a GitHub Personal Access Token with:

- `read:packages`

Use your GitHub username and this token for `GHCR_USERNAME` and `GHCR_TOKEN` in the GitHub Actions secrets.

## 5. Add GitHub repository secrets

In GitHub:

`Repository -> Settings -> Secrets and variables -> Actions`

Add these secrets:

- `GCP_VM_HOST`: your VM external IP or DNS
- `GCP_VM_USER`: your SSH username
- `GCP_VM_SSH_KEY`: private SSH key used by GitHub Actions
- `GCP_VM_PORT`: usually `22`
- `GCP_VM_APP_DIR`: example `/opt/marketgrid`
- `GHCR_USERNAME`: your GitHub username
- `GHCR_TOKEN`: GitHub token with `read:packages`

## 6. Push the first deployment

Push to `main`.

What happens:

1. `ci.yml` builds the frontend, installs backend dependencies, compiles Python sources, and validates both compose files.
2. `cd.yml` builds and pushes:
   - `ghcr.io/<owner>/<repo>-backend:<git-sha>`
   - `ghcr.io/<owner>/<repo>-frontend:<git-sha>`
   - `latest` tags for both images
3. The deploy job copies deployment files to the VM and runs:

```bash
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml pull
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml up -d
```

## 7. Verify on the VM

SSH into the VM and check:

```bash
cd /opt/marketgrid
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml ps
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml logs -f backend
```

Open:

- `http://<VM_EXTERNAL_IP>`

## 8. Useful rollback

If a deployment is bad, edit `/opt/marketgrid/.env.prod`:

```env
IMAGE_TAG=<older-commit-sha>
```

Then redeploy manually:

```bash
cd /opt/marketgrid
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml pull
docker compose --env-file .env.prod -f deploy/docker-compose.prod.yml up -d
```
