# Deployment Guide: ChestX-ray AI Assist

This guide covers deployment instructions for the **ChestX-ray AI Assist** prototype across containerized (Docker & Docker Compose), Cloud VM, and local environments.

---

## 1. Containerized Deployment (Docker & Docker Compose) - Recommended

The project includes a **multi-stage Docker build** that:
1. Compiles the React + TypeScript frontend into optimized static assets.
2. Sets up Python 3.11 with PyTorch, Torchvision, pydicom, and FastAPI backend.
3. Packages both into a single production container where FastAPI serves both the web UI and `/api/v1` endpoints on a single port.
4. Automatically checks and converts model checkpoints to safetensors on boot if needed.

### Prerequisites
- [Docker Engine & Docker Compose](https://docs.docker.com/get-docker/) (or Docker Desktop on Windows/macOS).
- Minimum recommended hardware: 4 GB RAM, 2 vCPUs, and ~10 GB free disk space.

### Step-by-Step Instructions

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Generate a random secret for JWT authentication and update `JWT_SECRET` in `.env`:
   ```bash
   # On Linux/macOS:
   openssl rand -hex 32
   # On Windows PowerShell:
   [System.Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
   ```

2. **Build and Launch Container**:
   ```bash
   docker compose up --build -d
   ```

3. **Verify Deployment**:
   Check container status and logs:
   ```bash
   docker compose ps
   docker compose logs -f
   ```
   Test the health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   You should see:
   ```json
   {"status":"ok","models_ready":{"baseline":true,"A":true,"B":true,"C":true,"D":true},...}
   ```

4. **Access the Web Application**:
   - Open [http://localhost:8000](http://localhost:8000) in your browser.
   - **First-run Admin Setup**: If this is your first time launching, create the administrator account (requires a password of at least 12 characters).
   - Log in and start reviewing chest X-ray analyses.

5. **Stop or Restart**:
   ```bash
   # Stop container
   docker compose down

   # Restart container
   docker compose restart
   ```

---

## 2. Cloud VM Deployment (AWS EC2, GCP, Azure, DigitalOcean)

When deploying to a public cloud virtual machine:

### 1. Provision VM
- **Recommended Spec**: `t3.medium` / `t4g.medium` (AWS) or `e2-standard-2` (GCP) (2 vCPUs, 4–8 GB RAM). GPU is optional; ResNet-18 CPU inference is fast (~100–250ms per X-ray).
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS.
- **Firewall/Security Group**: Allow incoming traffic on ports `80` (HTTP), `443` (HTTPS), and `22` (SSH).

### 2. Install Docker on Ubuntu
```bash
sudo apt update && sudo apt install -y git curl
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Clone Repository and Configure
```bash
git clone https://github.com/AryanAkhare/RareChest-GAN.git
cd RareChest-GAN
cp .env.example .env
# Edit .env with your custom JWT_SECRET
nano .env
```

### 4. Run with Docker Compose
```bash
docker compose up --build -d
```

### 5. Setup Reverse Proxy & SSL (Nginx + Let's Encrypt)
To expose the application securely over HTTPS with your custom domain:

Install Nginx and Certbot:
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/chestxray`:
```nginx
server {
    server_name yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and obtain SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/chestxray /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 3. Direct Local / Bare-Metal Deployment (Without Docker)

If you prefer running directly on a host with Python and Node.js:

1. **Prerequisites**:
   - Python 3.10+ (Python 3.11 recommended)
   - Node.js 20+ and npm

2. **Setup Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r backend/requirements.txt
   ```

3. **Convert Checkpoint Weights** (Run once):
   ```bash
   python scripts/convert_checkpoints.py
   ```

4. **Build the Frontend Assets**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. **Start the Production Application**:
   ```bash
   # Windows:
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   # Linux/macOS:
   python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
   Open `http://localhost:8000` in your web browser.

---

## 4. Production Security & Data Persistence

1. **Data Volume (`./data`)**:
   - The `./data` folder contains `local.db` (SQLite audit logs, users, feedback, analysis records) and `converted/` (safetensors models).
   - Ensure `./data` is backed up regularly in production.
2. **Network Isolation & Privacy**:
   - Uploaded X-ray image pixels are processed in memory and never stored directly in the database.
   - For clinical research confidentiality, ensure firewall rules or VPNs restrict access to authorized personnel.
3. **Regulatory Notice**:
   - This system is a research and education prototype. As stated in the disclaimer, it is not an FDA-cleared medical device and must not be used as a standalone diagnostic tool.
