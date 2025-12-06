# Contributing to PaaS Platform

Merci de votre intérêt pour contribuer à PaaS Platform ! Ce document fournit des lignes directrices pour contribuer au projet.

## Table des Matières

1. [Code of Conduct](#code-of-conduct)
2. [Comment contribuer](#comment-contribuer)
3. [Soumettre des changements](#soumettre-des-changements)
4. [Standards de code](#standards-de-code)
5. [Tests](#tests)
6. [Documentation](#documentation)

## Code of Conduct

En participant à ce projet, vous acceptez de maintenir un environnement respectueux et inclusif pour tous.

## Comment contribuer

### Rapporter des bugs

Avant de créer une issue :
1. Vérifiez qu'une issue similaire n'existe pas déjà
2. Collectez les informations suivantes :
   - Version de l'application
   - Version de Proxmox
   - Version de Python et Terraform
   - Logs d'erreur complets

**Format d'une issue bug** :

```markdown
**Description du bug**
Une description claire du problème.

**Étapes pour reproduire**
1. Aller à '...'
2. Cliquer sur '...'
3. Voir l'erreur

**Comportement attendu**
Ce qui devrait se passer.

**Comportement actuel**
Ce qui se passe réellement.

**Environnement**
- OS: [e.g. Ubuntu 22.04]
- Proxmox Version: [e.g. 7.4]
- Python Version: [e.g. 3.10]
- Terraform Version: [e.g. 1.5.0]

**Logs**
```
Insérer les logs pertinents
```
```

### Suggérer des fonctionnalités

**Format d'une issue feature** :

```markdown
**Description de la fonctionnalité**
Une description claire de la fonctionnalité proposée.

**Problème résolu**
Quel problème cette fonctionnalité résout-elle ?

**Solution proposée**
Comment vous imaginez que cela devrait fonctionner.

**Alternatives considérées**
Quelles autres solutions avez-vous envisagées ?
```

### Contribuer du code

1. **Fork le repository**
   ```bash
   git clone https://github.com/votre-username/paas-platform.git
   cd paas-platform
   ```

2. **Créer une branche**
   ```bash
   git checkout -b feature/ma-nouvelle-fonctionnalite
   # ou
   git checkout -b fix/correction-bug
   ```

3. **Faire vos changements**
   - Suivez les [standards de code](#standards-de-code)
   - Ajoutez des tests si nécessaire
   - Mettez à jour la documentation

4. **Commit vos changements**
   ```bash
   git add .
   git commit -m "feat: ajouter support pour Kubernetes"
   ```

   **Format des commits** :
   - `feat:` Nouvelle fonctionnalité
   - `fix:` Correction de bug
   - `docs:` Changements de documentation
   - `style:` Formatage, points-virgules manquants, etc.
   - `refactor:` Refactorisation du code
   - `test:` Ajout de tests
   - `chore:` Tâches de maintenance

5. **Push vers votre fork**
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```

6. **Créer une Pull Request**
   - Allez sur GitHub
   - Créez une Pull Request depuis votre branche
   - Remplissez le template de PR

## Soumettre des changements

### Pull Request Process

1. **Avant de soumettre** :
   - Assurez-vous que tous les tests passent
   - Vérifiez que le code respecte les standards
   - Mettez à jour la documentation si nécessaire
   - Ajoutez des tests pour les nouvelles fonctionnalités

2. **Description de la PR** :
   ```markdown
   ## Description
   Brève description des changements.

   ## Type de changement
   - [ ] Bug fix
   - [ ] Nouvelle fonctionnalité
   - [ ] Breaking change
   - [ ] Documentation

   ## Tests
   - [ ] Tests unitaires ajoutés/modifiés
   - [ ] Tests manuels effectués
   - [ ] Tous les tests passent

   ## Checklist
   - [ ] Code respecte les standards
   - [ ] Documentation mise à jour
   - [ ] Changements testés localement
   - [ ] Pas de warnings/erreurs
   ```

3. **Review** :
   - Attendez la review des mainteneurs
   - Répondez aux commentaires
   - Effectuez les changements demandés

## Standards de code

### Python

Suivez **PEP 8** :

```python
# Bon
def create_deployment(name: str, deployment_type: str) -> Dict[str, Any]:
    """
    Create a new deployment.
    
    Args:
        name: Deployment name
        deployment_type: Type of deployment ('vm' or 'lxc')
    
    Returns:
        Dictionary with deployment details
    """
    # Implementation
    pass

# Mauvais
def createDeployment(name,type):
    pass
```

**Règles** :
- Utilisez 4 espaces pour l'indentation
- Lignes max 100 caractères
- Docstrings pour toutes les fonctions publiques
- Type hints pour les paramètres et retours
- Snake_case pour les fonctions et variables
- PascalCase pour les classes

### JavaScript

Suivez **ES6+** :

```javascript
// Bon
const createDeployment = async (deploymentData) => {
    try {
        const response = await fetch('/api/deploy', {
            method: 'POST',
            body: JSON.stringify(deploymentData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

// Mauvais
function createDeployment(deploymentData) {
    // ...
}
```

**Règles** :
- Utilisez const/let, pas var
- Arrow functions préférées
- Async/await pour les opérations asynchrones
- CamelCase pour les variables et fonctions

### HTML/CSS

```html
<!-- Bon -->
<div class="card">
    <h2 class="card-title">Titre</h2>
    <p class="card-description">Description</p>
</div>
```

```css
/* Bon */
.card {
    background: var(--bg-card);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
}
```

**Règles** :
- Indentation de 4 espaces
- Classes sémantiques
- Utilisez les variables CSS
- BEM naming convention (optionnel)

### Terraform

```hcl
# Bon
resource "proxmox_vm_qemu" "deployment_vm" {
  count = var.deployment_type == "vm" ? 1 : 0
  
  name        = var.deployment_name
  target_node = var.proxmox_node
  
  cores  = var.cores
  memory = var.memory
}
```

**Règles** :
- Indentation de 2 espaces
- Variables en snake_case
- Commentaires pour les ressources complexes

## Tests

### Écrire des tests

```python
# tests/test_deployment.py
import pytest
from backend.models.deployment import Deployment, DeploymentStatus

def test_create_deployment():
    """Test deployment creation"""
    deployment = Deployment(
        name="test-app",
        deployment_type="vm",
        framework="django",
        github_url="https://github.com/test/repo",
        resources={"cores": 2, "memory": 2048, "disk": 20},
        status=DeploymentStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    assert deployment.name == "test-app"
    assert deployment.deployment_type == "vm"
    assert deployment.status == DeploymentStatus.PENDING
```

### Lancer les tests

```bash
# Installer pytest
pip install pytest pytest-cov

# Lancer tous les tests
pytest

# Avec coverage
pytest --cov=backend tests/

# Tests spécifiques
pytest tests/test_deployment.py
```

## Documentation

### Docstrings Python

```python
def deploy_application(name: str, framework: str, github_url: str) -> Dict[str, Any]:
    """
    Deploy an application from GitHub.
    
    This function handles the complete deployment process including:
    - Infrastructure provisioning
    - Application cloning
    - Dependency installation
    
    Args:
        name: The deployment name (alphanumeric, 3-50 chars)
        framework: Framework identifier (e.g., 'django', 'laravel')
        github_url: Valid GitHub repository URL
    
    Returns:
        Dictionary containing:
            - success (bool): Whether deployment succeeded
            - deployment_id (str): UUID of the deployment
            - ip_address (str): Assigned IP address
    
    Raises:
        ValueError: If parameters are invalid
        TerraformError: If infrastructure provisioning fails
    
    Example:
        >>> result = deploy_application(
        ...     name="my-app",
        ...     framework="django",
        ...     github_url="https://github.com/user/repo"
        ... )
        >>> print(result['ip_address'])
        '192.168.100.10'
    """
    # Implementation
```

### Commenter le code

```python
# Bon : Explique le "pourquoi"
# Use VM instead of LXC for applications requiring kernel modules
if requires_kernel_modules:
    deployment_type = 'vm'

# Mauvais : Explique le "quoi" (évident)
# Set deployment type to vm
deployment_type = 'vm'
```

### README Updates

Quand vous ajoutez une fonctionnalité, mettez à jour :
- `README.md` : Si c'est une fonctionnalité majeure
- `docs/API.md` : Si vous ajoutez/modifiez des endpoints
- `QUICKSTART.md` : Si cela affecte l'installation/utilisation
- `docs/PROXMOX_SETUP.md` : Si cela nécessite une config Proxmox

## Setup Environnement de Développement

```bash
# Clone du repository
git clone https://github.com/votre-username/paas-platform.git
cd paas-platform

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe

# Copier la configuration
cp .env.example .env

# Lancer en mode développement
python app.py
```

## Questions ?

Si vous avez des questions sur la contribution :
- Ouvrez une issue avec le label `question`
- Consultez les issues existantes
- Contactez les mainteneurs

## Licence

En contribuant, vous acceptez que vos contributions soient sous la même licence MIT que le projet.

Merci de contribuer à PaaS Platform ! 🚀
