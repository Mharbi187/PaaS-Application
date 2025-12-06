# Configuration de la Base de Données

## Vue d'ensemble

La plateforme PaaS utilise **SQLAlchemy** comme ORM (Object-Relational Mapping) pour gérer les déploiements et les données de configuration. La base de données stocke les informations sur les déploiements, leurs statuts et leurs ressources.

## Architecture de la Base de Données

### Modèle Deployment

Le modèle principal `Deployment` représente chaque application déployée avec les informations suivantes :

```
Deployment
├── id (UUID) - Identifiant unique
├── name (String) - Nom du déploiement
├── deployment_type (String) - 'vm' ou 'lxc'
├── framework (String) - Framework utilisé (Django, Flask, Express, etc.)
├── github_url (String) - URL du dépôt GitHub
├── resources (JSON) - Ressources allouées (CPU, mémoire, disque)
├── status (String) - État du déploiement (PENDING, PROVISIONING, DEPLOYING, RUNNING, FAILED, etc.)
├── created_at (DateTime) - Date de création
├── deployed_at (DateTime) - Date de déploiement
├── deleted_at (DateTime) - Date de suppression
├── ip_address (String) - Adresse IP de la VM/LXC
├── vm_id (Integer) - ID Proxmox
├── error_message (Text) - Message d'erreur si applicable
├── user_id (String) - Utilisateur propriétaire (futur support multi-utilisateurs)
└── tags (String) - Tags pour classification
```

## Installation et Configuration

### 1. Installation des dépendances

Les dépendances pour la base de données sont déjà dans `requirements.txt`:

```bash
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
SQLAlchemy==2.0.23
```

### 2. Configuration

La configuration de la base de données se fait dans `config.py`:

```python
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///deployments.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

Pour utiliser une base de données différente, modifiez la variable `DATABASE_URL` dans `.env`:

**SQLite (défaut):**
```
DATABASE_URL=sqlite:///deployments.db
```

**PostgreSQL:**
```
DATABASE_URL=postgresql://username:password@localhost/paas_db
```

**MySQL:**
```
DATABASE_URL=mysql+pymysql://username:password@localhost/paas_db
```

## Gestion de la Base de Données

### Initialisation (Première installation)

**Bash:**
```bash
bash setup.sh
```

**PowerShell (Windows):**
```powershell
.\setup.ps1
```

Ou manuellement:

```bash
python manage_db.py init
```

### Commandes de gestion

Le script `manage_db.py` fournit plusieurs commandes :

#### Initialiser la base de données
```bash
python manage_db.py init
```
Crée les tables si elles n'existent pas.

#### Réinitialiser la base de données
```bash
python manage_db.py reset
```
⚠️ **Attention** : Supprime toutes les données et recrée les tables.

#### Remplir avec des données d'exemple
```bash
python manage_db.py seed
```
Ajoute des déploiements d'exemple pour tester.

#### Afficher les statistiques
```bash
python manage_db.py stats
```
Affiche le nombre total de déploiements, leur statut, etc.

## Migrations

### Créer une migration après modification du modèle

```bash
flask db migrate -m "Description of changes"
```

### Appliquer les migrations

```bash
flask db upgrade
```

### Revenir à une migration précédente

```bash
flask db downgrade
```

## Exemples d'utilisation

### Accéder à la base de données en Python

```python
from app import create_app, db
from backend.models.deployment_sqlalchemy import Deployment

app = create_app('development')

with app.app_context():
    # Créer un nouveau déploiement
    new_deployment = Deployment(
        name='my-app',
        deployment_type='vm',
        framework='django',
        github_url='https://github.com/user/repo',
        resources={'cores': 2, 'memory': 2048, 'disk': 20},
        status='running'
    )
    db.session.add(new_deployment)
    db.session.commit()
    
    # Récupérer tous les déploiements
    all_deployments = Deployment.get_all()
    
    # Récupérer par ID
    deployment = Deployment.get_by_id('deployment-id')
    
    # Récupérer par nom
    deployment = Deployment.get_by_name('my-app')
    
    # Récupérer par statut
    running = Deployment.get_by_status('running')
    
    # Afficher les statistiques
    total = Deployment.count_all()
    failed = Deployment.count_by_status('failed')
```

### Utiliser dans l'API Flask

Les routes API utilisent automatiquement les modèles SQLAlchemy:

```python
@api_bp.route('/deployments', methods=['GET'])
def list_deployments():
    deployments = Deployment.get_all()
    return jsonify({
        'success': True,
        'deployments': [d.to_dict() for d in deployments]
    })
```

## Sauvegarde et restauration

### Sauvegarder la base de données (SQLite)

```bash
cp deployments.db deployments.db.backup
```

### Sauvegarder la base de données (PostgreSQL)

```bash
pg_dump paas_db > paas_db.backup
```

### Restaurer la base de données (PostgreSQL)

```bash
psql paas_db < paas_db.backup
```

## Optimisation et performance

### Index sur les requêtes fréquentes

Les champs `name`, `status` et `created_at` sont déjà indexés pour optimiser les requêtes courantes.

### Paginação (futur)

Pour implémenter la pagination :

```python
from flask import request

page = request.args.get('page', 1, type=int)
per_page = 20

paginated = Deployment.query.paginate(page=page, per_page=per_page)
return jsonify({
    'total': paginated.total,
    'pages': paginated.pages,
    'deployments': [d.to_dict() for d in paginated.items]
})
```

## Dépannage

### Erreur de connexion à la base de données

- Vérifiez que `DATABASE_URL` est correctement configuré
- Pour SQLite, assurez-vous que le répertoire existe
- Pour PostgreSQL/MySQL, testez la connexion

### Migrations échouées

```bash
flask db downgrade  # Revenir à la version précédente
flask db upgrade    # Recommencer
```

### Réinitialiser complètement

```bash
rm deployments.db          # Supprimer la base SQLite
python manage_db.py init   # Réinitialiser
python manage_db.py seed   # Remplir avec des données d'exemple
```

## Ressources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-Migrate](https://flask-migrate.readthedocs.io/)
