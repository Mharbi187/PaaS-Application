# Plateforme PaaS Privée - Proxmox Edition

Une plateforme Platform-as-a-Service (PaaS) privée permettant le déploiement automatique d'applications à partir de dépôts GitHub sur une infrastructure Proxmox.

## 🎯 Fonctionnalités

- **Déploiement automatisé** : Créez des VMs ou conteneurs LXC en quelques clics
- **Support multi-frameworks** : Django, Laravel, Node.js, React, Vue.js, et plus
- **Intégration GitHub** : Déployez directement depuis vos dépôts
- **Infrastructure as Code** : Utilise Terraform pour la gestion de l'infrastructure
- **Interface Web moderne** : Interface utilisateur intuitive et responsive

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Web (Flask)                     │
│                     Port: 5000                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Backend (Flask)                       │
│              - Validation des entrées                        │
│              - Génération de configuration Terraform         │
│              - Exécution Terraform                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Terraform                               │
│              - Création VM/LXC                               │
│              - Configuration réseau                          │
│              - Provisioning                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox VE                                │
│              - Orchestration VMs                             │
│              - Gestion conteneurs LXC                        │
│              - Allocation ressources                         │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prérequis

- **Proxmox VE** 7.0+ installé et configuré
- **Python** 3.8+
- **Terraform** 1.5+
- **Node.js** 16+ (pour le frontend)
- Accès API Proxmox
- Connexion Internet pour télécharger les dépendances

## 🚀 Installation

### 1. Cloner le projet

```bash
cd "d:\Dev Projects\Paas Application"
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Configurer Proxmox

Créez un fichier `.env` à la racine du projet :

```env
PROXMOX_URL=https://your-proxmox-server:8006/api2/json
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password
PROXMOX_NODE=pve
PROXMOX_STORAGE=local-lvm
```

### 4. Initialiser Terraform

```bash
cd terraform
terraform init
```

### 5. Lancer l'application

```bash
python app.py
```

L'interface web sera accessible sur `http://localhost:5000`

## 📖 Utilisation

1. Accédez à l'interface web
2. Sélectionnez le type de déploiement (VM ou LXC)
3. Choisissez le framework de votre application
4. Entrez l'URL du dépôt GitHub
5. Configurez les ressources (CPU, RAM, Disque)
6. Cliquez sur "Déployer"
7. Récupérez l'adresse IP et les informations d'accès

## 🛠️ Frameworks Supportés

### Backend
- **Django** (Python)
- **Laravel** (PHP)
- **Express.js** (Node.js)
- **Flask** (Python)
- **FastAPI** (Python)

### Frontend
- **React**
- **Vue.js**
- **Angular**
- **Next.js**
- **Nuxt.js**

### Full-Stack
- **MERN** (MongoDB, Express, React, Node)
- **MEAN** (MongoDB, Express, Angular, Node)
- **LAMP** (Linux, Apache, MySQL, PHP)

## 📁 Structure du Projet

```
Paas Application/
├── app.py                      # Application Flask principale
├── config.py                   # Configuration de l'application
├── requirements.txt            # Dépendances Python
├── .env                        # Variables d'environnement
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # Routes API
│   │   └── terraform_manager.py  # Gestion Terraform
│   ├── models/
│   │   └── deployment.py      # Modèles de données
│   └── utils/
│       ├── validators.py      # Validation des entrées
│       └── helpers.py         # Fonctions utilitaires
├── terraform/
│   ├── main.tf                # Configuration principale
│   ├── variables.tf           # Variables Terraform
│   ├── outputs.tf             # Sorties Terraform
│   └── modules/
│       ├── vm/                # Module VM
│       └── lxc/               # Module LXC
├── scripts/
│   ├── install_framework.sh   # Installation des frameworks
│   └── deploy_app.sh          # Déploiement de l'application
├── static/
│   ├── css/
│   │   └── style.css          # Styles CSS
│   ├── js/
│   │   └── app.js             # JavaScript frontend
│   └── images/
└── templates/
    ├── index.html             # Page principale
    ├── dashboard.html         # Tableau de bord
    └── deployment.html        # Page de déploiement
```

## 🔒 Sécurité

- Les credentials Proxmox sont stockés dans des variables d'environnement
- Validation stricte des entrées utilisateur
- Isolation des déploiements
- Logs d'audit pour toutes les opérations

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou soumettre une pull request.

## 📄 Licence

Ce projet est sous licence Mohamed Harbi


