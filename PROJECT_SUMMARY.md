# 🏗️ PaaS Application — Project Summary

## Overview

This is a **Private Platform-as-a-Service (PaaS)** application that enables **automated deployment of web applications** directly onto a **Proxmox VE** virtualization infrastructure. It essentially allows users to deploy their GitHub projects into isolated VMs or LXC containers with just a few clicks.

---

## 🎯 Core Purpose

| Aspect | Description |
|--------|-------------|
| **What it does** | Automates the deployment of applications from GitHub to Proxmox VMs/LXC containers |
| **Target Users** | Developers or DevOps teams with private Proxmox infrastructure |
| **Main Benefit** | Eliminates manual server setup — users only need to provide a GitHub URL and choose resources |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python) |
| **Frontend** | Jinja2 Templates, Vanilla JS, Custom CSS |
| **Database** | SQLite via SQLAlchemy |
| **Infrastructure as Code** | Terraform (with `bpg/proxmox` provider) |
| **Virtualization** | Proxmox VE (VMs & LXC containers) |
| **Configuration** | Environment variables via `.env` |

---

## 📐 Architecture Flow

```
┌──────────────────────┐
│   Web Interface      │  ← User fills deployment form
│   (Flask Templates)  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   Flask REST API     │  ← Validates input, creates Deployment record
│   (routes.py)        │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  Terraform Manager   │  ← Generates Terraform config (.tf files)
│(terraform_manager.py)│     Executes: terraform init → plan → apply
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   Proxmox VE         │  ← Creates VM or LXC container
│   (via Terraform)    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   SSH Provisioning   │  ← Clones GitHub repo, installs dependencies
│   (paramiko/SSH)     │     Runs framework-specific commands
└──────────────────────┘
```

---

## 🔑 Key Functionalities

### 1. **Deployment Creation**
- User selects:
  - **Deployment type**: VM or LXC container
  - **Framework**: Django, Flask, Laravel, Express.js, React, Vue.js, Next.js, etc.
  - **GitHub URL**: Repository to deploy
  - **Resources**: CPU cores, RAM, disk size
- System then:
  1. Creates a DB record with status `PENDING`
  2. Generates Terraform configuration
  3. Runs `terraform apply` to provision infrastructure
  4. Gets the IP address from Proxmox
  5. Connects via SSH to install dependencies and deploy the app
  6. Updates the deployment status to `RUNNING`

### 2. **Deployment Management**
- **List deployments**: View all current deployments with status
- **Get deployment details**: View IP, VM ID, resources, status
- **Delete deployment**: Runs `terraform destroy` to tear down infrastructure
- **View logs**: Access Terraform execution logs

### 3. **Proxmox Sync**
- **Sync existing VMs/LXCs**: Import VMs already on Proxmox into the dashboard
- **View Proxmox resources**: List all VMs and containers from Proxmox API

### 4. **Statistics Dashboard**
- Total deployments count
- Active deployments count
- Success rate percentage

---

## 📦 Supported Frameworks

| Category | Frameworks |
|----------|------------|
| **Python** | Django, Flask, FastAPI |
| **PHP** | Laravel |
| **Node.js** | Express.js, React, Vue.js, Next.js |
| **Full-Stack** | MERN, MEAN, LAMP |

Each framework has predefined:
- Default port
- Installation commands
- Language runtime requirements

---

## 🗂️ Key Files & Their Roles

| File | Purpose |
|------|---------|
| `app.py` | Flask application factory, main entry point |
| `config.py` | Configuration management (env vars, Proxmox settings, framework definitions) |
| `backend/api/routes.py` | REST API endpoints (`/api/deploy`, `/api/deployments`, etc.) |
| `backend/api/terraform_manager.py` | Generates Terraform configs, executes Terraform, handles SSH provisioning |
| `backend/models/deployment.py` | SQLAlchemy model for deployment records |
| `terraform/main.tf` | Terraform template for VM/LXC provisioning on Proxmox |
| `templates/*.html` | Frontend pages (index, dashboard, deployment form) |
| `static/css/style.css` | Custom CSS styling |
| `static/js/app.js` | Frontend JavaScript logic |

---

## 🔒 Security Considerations

1. **Credential Management**: Proxmox credentials stored in `.env` (excluded from git)
2. **Input Validation**: User inputs validated before Terraform execution
3. **SSH Key Generation**: Auto-generates SSH keypairs if not provided
4. **Isolated Deployments**: Each deployment gets its own VM/LXC container
5. **Audit Logging**: Operations logged to `logs/paas.log`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/frameworks` | List supported frameworks |
| `POST` | `/api/deploy` | Create new deployment |
| `GET` | `/api/deployments` | List all deployments |
| `GET` | `/api/deployments/<id>` | Get deployment details |
| `DELETE` | `/api/deployments/<id>` | Delete deployment |
| `GET` | `/api/deployments/<id>/logs` | Get deployment logs |
| `GET` | `/api/statistics` | Get platform statistics |
| `GET` | `/api/proxmox/resources` | Get Proxmox VMs/LXCs |
| `POST` | `/api/proxmox/sync` | Sync Proxmox resources to dashboard |

---

## 🎨 User Interface

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` | Landing page with features, stats, and framework list |
| **Dashboard** | `/dashboard` | View and manage all deployments |
| **Deploy** | `/deploy` | Form to create new deployments |

---

## 🚀 Running the Application

### Prerequisites
- Python 3.8+
- Proxmox VE 7.0+
- Terraform 1.5+
- Configured `.env` file with Proxmox credentials

### Quick Start
```bash
# Using existing virtual environment
.\.venv\Scripts\python.exe app.py

# Or using the batch script
start_paas.bat
```

The application will be available at `http://localhost:5000`

---

## 📊 Deployment Status Lifecycle

```
PENDING → PROVISIONING → DEPLOYING → RUNNING
                ↓              ↓
              FAILED         FAILED
                             
RUNNING → STOPPED → DELETED
```

---

## 📝 Notes

- This project combines **Infrastructure as Code** (Terraform) with a **user-friendly web interface** to abstract away the complexity of provisioning servers and deploying applications.
- The application supports both **VM** and **LXC container** deployments, giving flexibility based on resource needs.
- All deployments are automatically tracked in a SQLite database for easy management.

---

*Generated on: December 12, 2025*
