"""
Unit Tests for PaaS Platform
Run with: pytest tests/
"""

import pytest
from datetime import datetime
from backend.models.deployment import Deployment, DeploymentStatus
from backend.utils.validators import (
    validate_deployment_name,
    validate_github_url,
    validate_resources
)


class TestDeploymentModel:
    """Test Deployment model"""
    
    def test_create_deployment(self):
        """Test creating a deployment"""
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
        assert deployment.framework == "django"
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.ip_address is None
        assert deployment.vm_id is None
    
    def test_deployment_to_dict(self):
        """Test converting deployment to dictionary"""
        deployment = Deployment(
            name="test-app",
            deployment_type="vm",
            framework="django",
            github_url="https://github.com/test/repo",
            resources={"cores": 2, "memory": 2048, "disk": 20},
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        data = deployment.to_dict()
        
        assert data['name'] == "test-app"
        assert data['deployment_type'] == "vm"
        assert data['framework'] == "django"
        assert data['status'] == "pending"
    
    def test_get_deployment_by_id(self):
        """Test retrieving deployment by ID"""
        deployment = Deployment(
            name="test-app",
            deployment_type="vm",
            framework="django",
            github_url="https://github.com/test/repo",
            resources={"cores": 2, "memory": 2048, "disk": 20},
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        retrieved = Deployment.get_by_id(deployment.id)
        assert retrieved is not None
        assert retrieved.name == "test-app"
    
    def test_count_deployments(self):
        """Test counting deployments"""
        initial_count = Deployment.count_all()
        
        Deployment(
            name="test-app-1",
            deployment_type="vm",
            framework="django",
            github_url="https://github.com/test/repo",
            resources={"cores": 2, "memory": 2048, "disk": 20},
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        assert Deployment.count_all() == initial_count + 1


class TestValidators:
    """Test validation functions"""
    
    def test_validate_deployment_name_valid(self):
        """Test valid deployment names"""
        assert validate_deployment_name("my-app") is True
        assert validate_deployment_name("my_app_123") is True
        assert validate_deployment_name("app-test-01") is True
    
    def test_validate_deployment_name_invalid(self):
        """Test invalid deployment names"""
        assert validate_deployment_name("ab") is False  # Too short
        assert validate_deployment_name("a" * 51) is False  # Too long
        assert validate_deployment_name("my app") is False  # Contains space
        assert validate_deployment_name("my@app") is False  # Invalid character
        assert validate_deployment_name("") is False  # Empty
    
    def test_validate_github_url_valid(self):
        """Test valid GitHub URLs"""
        assert validate_github_url("https://github.com/user/repo") is True
        assert validate_github_url("https://github.com/user/repo-name") is True
        assert validate_github_url("http://github.com/user/my.repo") is True
    
    def test_validate_github_url_invalid(self):
        """Test invalid GitHub URLs"""
        assert validate_github_url("github.com/user/repo") is False  # No protocol
        assert validate_github_url("https://gitlab.com/user/repo") is False  # Not GitHub
        assert validate_github_url("https://github.com/user") is False  # No repo
        assert validate_github_url("") is False  # Empty
    
    def test_validate_resources_vm_valid(self):
        """Test valid VM resources"""
        resources = {
            "cores": 2,
            "memory": 2048,
            "disk": 20
        }
        errors = validate_resources(resources, "vm")
        assert len(errors) == 0
    
    def test_validate_resources_vm_invalid(self):
        """Test invalid VM resources"""
        resources = {
            "cores": 20,  # Too many
            "memory": 50000,  # Too much
            "disk": 5  # Too small
        }
        errors = validate_resources(resources, "vm")
        assert len(errors) > 0
    
    def test_validate_resources_lxc_valid(self):
        """Test valid LXC resources"""
        resources = {
            "cores": 2,
            "memory": 1024,
            "disk": 10
        }
        errors = validate_resources(resources, "lxc")
        assert len(errors) == 0
    
    def test_validate_resources_lxc_invalid(self):
        """Test invalid LXC resources"""
        resources = {
            "cores": 10,  # Too many for LXC
            "memory": 20000,  # Too much
            "disk": 3  # Too small
        }
        errors = validate_resources(resources, "lxc")
        assert len(errors) > 0


class TestHelpers:
    """Test helper functions"""
    
    def test_format_memory(self):
        """Test memory formatting"""
        from backend.utils.helpers import format_memory
        
        assert format_memory(512) == "512 MB"
        assert format_memory(1024) == "1.0 GB"
        assert format_memory(2048) == "2.0 GB"
    
    def test_parse_github_url(self):
        """Test GitHub URL parsing"""
        from backend.utils.helpers import parse_github_url
        
        result = parse_github_url("https://github.com/user/repo")
        assert result['owner'] == "user"
        assert result['repo'] == "repo"
        
        result = parse_github_url("https://github.com/django/django.git")
        assert result['owner'] == "django"
        assert result['repo'] == "django"
    
    def test_sanitize_name(self):
        """Test name sanitization"""
        from backend.utils.helpers import sanitize_name
        
        assert sanitize_name("My App Test") == "my-app-test"
        assert sanitize_name("Test@App#123") == "testapp123"
        assert sanitize_name("UPPERCASE") == "uppercase"


# Fixtures
@pytest.fixture
def sample_deployment():
    """Fixture for creating a sample deployment"""
    return Deployment(
        name="test-fixture-app",
        deployment_type="vm",
        framework="django",
        github_url="https://github.com/test/repo",
        resources={"cores": 2, "memory": 2048, "disk": 20},
        status=DeploymentStatus.PENDING,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_deployment_data():
    """Fixture for sample deployment data"""
    return {
        "name": "test-app",
        "deployment_type": "vm",
        "framework": "django",
        "github_url": "https://github.com/test/repo",
        "resources": {
            "cores": 2,
            "memory": 2048,
            "disk": 20
        }
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
