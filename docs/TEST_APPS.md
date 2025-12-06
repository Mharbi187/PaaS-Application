# Exemples d'Applications pour Tests

Ce dossier contient des exemples d'applications pour tester les déploiements sur différents frameworks.

## Applications de Test Disponibles

### 1. Django Simple Blog

**Repository**: https://github.com/example/django-simple-blog
**Framework**: Django
**Type recommandé**: VM
**Ressources recommandées**:
- Cores: 2
- Memory: 2048 MB
- Disk: 20 GB

### 2. Laravel API REST

**Repository**: https://github.com/example/laravel-rest-api
**Framework**: Laravel
**Type recommandé**: VM
**Ressources recommandées**:
- Cores: 2
- Memory: 2048 MB
- Disk: 20 GB

### 3. Express.js API

**Repository**: https://github.com/example/express-api
**Framework**: Express
**Type recommandé**: LXC
**Ressources recommandées**:
- Cores: 1
- Memory: 1024 MB
- Disk: 10 GB

### 4. React Dashboard

**Repository**: https://github.com/facebook/create-react-app
**Framework**: React
**Type recommandé**: LXC
**Ressources recommandées**:
- Cores: 1
- Memory: 1024 MB
- Disk: 10 GB

### 5. Vue.js Application

**Repository**: https://github.com/vuejs/vue-next
**Framework**: Vue.js
**Type recommandé**: LXC
**Ressources recommandées**:
- Cores: 1
- Memory: 1024 MB
- Disk: 10 GB

## Créer Votre Propre Application de Test

### Structure Minimale Django

```
my-django-app/
├── requirements.txt
├── manage.py
├── wsgi.py
└── myapp/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    └── views.py
```

**requirements.txt**:
```
Django==4.2.0
gunicorn==21.2.0
```

### Structure Minimale Laravel

```
my-laravel-app/
├── composer.json
├── artisan
├── public/
│   └── index.php
├── app/
└── routes/
    └── web.php
```

### Structure Minimale Express

```
my-express-app/
├── package.json
├── index.js
└── routes/
    └── api.js
```

**package.json**:
```json
{
  "name": "my-express-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
```

**index.js**:
```javascript
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Hello from PaaS Platform!' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
```

## Tester un Déploiement

### Via l'Interface Web

1. Accédez à http://localhost:5000/deploy
2. Remplissez le formulaire avec une des applications de test
3. Cliquez sur "Déployer"

### Via l'API

```bash
curl -X POST http://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-express-app",
    "deployment_type": "lxc",
    "framework": "express",
    "github_url": "https://github.com/your-username/express-test-app",
    "resources": {
      "cores": 1,
      "memory": 1024,
      "disk": 10
    }
  }'
```

## Dépannage

Si le déploiement échoue :

1. Vérifiez les logs : `logs/paas.log`
2. Vérifiez que le dépôt GitHub est accessible
3. Vérifiez que le `requirements.txt` ou `package.json` existe
4. Vérifiez la configuration Proxmox

## Créer un Dépôt de Test

```bash
# Créer un nouveau dépôt
mkdir my-test-app
cd my-test-app
git init

# Ajouter une application Express simple
cat > index.js << EOF
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.json({ 
    message: 'Hello from PaaS Platform!',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(\`Server running on port \${port}\`);
});
EOF

# Ajouter package.json
cat > package.json << EOF
{
  "name": "paas-test-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
EOF

# Ajouter au Git
git add .
git commit -m "Initial commit"

# Pousser vers GitHub
git remote add origin https://github.com/your-username/my-test-app.git
git push -u origin main
```

Maintenant vous pouvez déployer cette application via la plateforme PaaS !
