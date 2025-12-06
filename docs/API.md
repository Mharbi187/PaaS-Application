# Documentation API - PaaS Platform

API REST pour la gestion des déploiements sur la plateforme PaaS.

## Base URL

```
http://localhost:5000/api
```

## Authentification

Actuellement, l'API ne nécessite pas d'authentification. Pour la production, ajoutez JWT ou API tokens.

## Endpoints

### Health Check

**GET** `/health`

Vérifier l'état de l'application.

**Réponse**
```json
{
  "status": "healthy",
  "service": "PaaS Platform",
  "version": "1.0.0"
}
```

---

### Frameworks

#### Obtenir la liste des frameworks supportés

**GET** `/api/frameworks`

**Réponse**
```json
{
  "success": true,
  "frameworks": {
    "django": {
      "name": "Django",
      "language": "python",
      "version": "4.2",
      "port": 8000,
      "install_cmd": "pip install django gunicorn"
    },
    "laravel": {
      "name": "Laravel",
      "language": "php",
      "version": "10.x",
      "port": 8000,
      "install_cmd": "composer global require laravel/installer"
    }
    // ... autres frameworks
  }
}
```

---

### Déploiements

#### Créer un nouveau déploiement

**POST** `/api/deploy`

**Body**
```json
{
  "name": "mon-application",
  "deployment_type": "vm",
  "framework": "django",
  "github_url": "https://github.com/username/repository",
  "resources": {
    "cores": 2,
    "memory": 2048,
    "disk": 20
  }
}
```

**Validation**
- `name`: 3-50 caractères alphanumériques, tirets et underscores
- `deployment_type`: "vm" ou "lxc"
- `framework`: Doit être dans la liste des frameworks supportés
- `github_url`: URL GitHub valide (https://github.com/owner/repo)
- `resources.cores`: 1-16 pour VM, 1-8 pour LXC
- `resources.memory`: 512-32768 MB pour VM, 256-16384 MB pour LXC
- `resources.disk`: 10-500 GB pour VM, 5-200 GB pour LXC

**Réponse Succès**
```json
{
  "success": true,
  "message": "Application deployed successfully",
  "deployment": {
    "id": "uuid-here",
    "name": "mon-application",
    "ip_address": "192.168.100.10",
    "vm_id": 100,
    "status": "running",
    "framework": "django",
    "access_url": "http://192.168.100.10:8000"
  }
}
```

**Réponse Erreur**
```json
{
  "success": false,
  "errors": [
    "Invalid deployment_type. Must be 'vm' or 'lxc'",
    "Invalid GitHub URL"
  ]
}
```

**Codes HTTP**
- `200`: Succès
- `400`: Erreur de validation
- `500`: Erreur serveur

---

#### Lister tous les déploiements

**GET** `/api/deployments`

**Réponse**
```json
{
  "success": true,
  "deployments": [
    {
      "id": "uuid-1",
      "name": "mon-app-1",
      "deployment_type": "vm",
      "framework": "django",
      "github_url": "https://github.com/user/repo",
      "resources": {
        "cores": 2,
        "memory": 2048,
        "disk": 20
      },
      "status": "running",
      "created_at": "2025-11-25T10:00:00Z",
      "deployed_at": "2025-11-25T10:05:32Z",
      "ip_address": "192.168.100.10",
      "vm_id": 100,
      "error_message": null
    }
  ]
}
```

---

#### Obtenir un déploiement spécifique

**GET** `/api/deployments/{deployment_id}`

**Paramètres**
- `deployment_id`: UUID du déploiement

**Réponse**
```json
{
  "success": true,
  "deployment": {
    "id": "uuid-1",
    "name": "mon-app-1",
    "deployment_type": "vm",
    "framework": "django",
    "status": "running",
    "ip_address": "192.168.100.10",
    "vm_id": 100
    // ... autres champs
  }
}
```

**Erreur - Non trouvé**
```json
{
  "success": false,
  "error": "Deployment not found"
}
```

---

#### Supprimer un déploiement

**DELETE** `/api/deployments/{deployment_id}`

**Paramètres**
- `deployment_id`: UUID du déploiement

**Réponse**
```json
{
  "success": true,
  "message": "Deployment deleted successfully"
}
```

**Notes**
- Cette action détruit l'infrastructure Terraform
- La suppression est irréversible

---

#### Obtenir les logs d'un déploiement

**GET** `/api/deployments/{deployment_id}/logs`

**Paramètres**
- `deployment_id`: UUID du déploiement

**Réponse**
```json
{
  "success": true,
  "logs": "Terraform logs content here..."
}
```

---

### Statistiques

#### Obtenir les statistiques de la plateforme

**GET** `/api/stats`

**Réponse**
```json
{
  "success": true,
  "stats": {
    "total_deployments": 15,
    "running_deployments": 12,
    "failed_deployments": 2,
    "success_rate": 80.0
  }
}
```

---

## États des Déploiements

| État | Description |
|------|-------------|
| `pending` | Déploiement en attente |
| `provisioning` | Infrastructure en cours de création |
| `deploying` | Application en cours de déploiement |
| `running` | Application déployée et en cours d'exécution |
| `failed` | Échec du déploiement |
| `stopped` | Déploiement arrêté |
| `deleted` | Déploiement supprimé |

---

## Exemples d'utilisation

### cURL

**Créer un déploiement**
```bash
curl -X POST http://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-django",
    "deployment_type": "vm",
    "framework": "django",
    "github_url": "https://github.com/django/django-example",
    "resources": {
      "cores": 2,
      "memory": 2048,
      "disk": 20
    }
  }'
```

**Lister les déploiements**
```bash
curl http://localhost:5000/api/deployments
```

**Supprimer un déploiement**
```bash
curl -X DELETE http://localhost:5000/api/deployments/uuid-here
```

### Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:5000/api"

# Créer un déploiement
deployment = {
    "name": "my-app",
    "deployment_type": "vm",
    "framework": "django",
    "github_url": "https://github.com/user/repo",
    "resources": {
        "cores": 2,
        "memory": 2048,
        "disk": 20
    }
}

response = requests.post(f"{BASE_URL}/deploy", json=deployment)
print(response.json())

# Lister les déploiements
response = requests.get(f"{BASE_URL}/deployments")
deployments = response.json()
print(deployments)
```

### JavaScript

```javascript
// Créer un déploiement
const createDeployment = async () => {
  const response = await fetch('http://localhost:5000/api/deploy', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'my-app',
      deployment_type: 'vm',
      framework: 'django',
      github_url: 'https://github.com/user/repo',
      resources: {
        cores: 2,
        memory: 2048,
        disk: 20
      }
    })
  });
  
  const data = await response.json();
  console.log(data);
};

// Lister les déploiements
const listDeployments = async () => {
  const response = await fetch('http://localhost:5000/api/deployments');
  const data = await response.json();
  console.log(data);
};
```

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 400 | Requête invalide (erreur de validation) |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur interne |

---

## Limite de taux (Rate Limiting)

Actuellement non implémenté. Pour la production, considérez d'ajouter :
- Limite par IP : 100 requêtes/minute
- Limite par utilisateur : 1000 requêtes/heure

---

## Webhooks (Futur)

Fonctionnalité planifiée pour recevoir des notifications :
- Déploiement terminé
- Déploiement échoué
- Mise à jour de statut

---

## Versioning

Version actuelle : **v1**

Les futures versions seront accessibles via :
```
/api/v2/...
```

---

## Support

Pour des questions ou problèmes avec l'API, consultez :
- Documentation : `README.md`
- Issues GitHub
- Logs : `logs/paas.log`
