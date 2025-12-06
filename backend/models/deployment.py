"""
Deployment Model
Represents a deployment in the PaaS platform
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = 'pending'
    PROVISIONING = 'provisioning'
    DEPLOYING = 'deploying'
    RUNNING = 'running'
    FAILED = 'failed'
    STOPPED = 'stopped'
    DELETED = 'deleted'


class Deployment:
    """Deployment model class"""
    
    # In-memory storage (replace with database in production)
    _deployments: Dict[str, 'Deployment'] = {}
    
    def __init__(
        self,
        name: str,
        deployment_type: str,
        framework: str,
        github_url: str,
        resources: Dict[str, Any],
        status: DeploymentStatus,
        created_at: datetime,
        id: Optional[str] = None
    ):
        """
        Initialize a deployment
        
        Args:
            name: Deployment name
            deployment_type: 'vm' or 'lxc'
            framework: Framework identifier
            github_url: GitHub repository URL
            resources: Resource specifications
            status: Current status
            created_at: Creation timestamp
            id: Optional deployment ID (generated if not provided)
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.deployment_type = deployment_type
        self.framework = framework
        self.github_url = github_url
        self.resources = resources
        self.status = status
        self.created_at = created_at
        self.deployed_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None
        self.ip_address: Optional[str] = None
        self.vm_id: Optional[int] = None
        self.error_message: Optional[str] = None
        
        # Save to storage
        Deployment._deployments[self.id] = self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert deployment to dictionary
        
        Returns:
            Dictionary representation of deployment
        """
        return {
            'id': self.id,
            'name': self.name,
            'deployment_type': self.deployment_type,
            'framework': self.framework,
            'github_url': self.github_url,
            'resources': self.resources,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'ip_address': self.ip_address,
            'vm_id': self.vm_id,
            'error_message': self.error_message
        }
    
    @classmethod
    def get_by_id(cls, deployment_id: str) -> Optional['Deployment']:
        """
        Get deployment by ID
        
        Args:
            deployment_id: Deployment identifier
        
        Returns:
            Deployment instance or None
        """
        return cls._deployments.get(deployment_id)
    
    @classmethod
    def get_all(cls) -> List['Deployment']:
        """
        Get all deployments
        
        Returns:
            List of all deployments
        """
        return list(cls._deployments.values())
    
    @classmethod
    def count_all(cls) -> int:
        """
        Count all deployments
        
        Returns:
            Total number of deployments
        """
        return len(cls._deployments)
    
    @classmethod
    def count_by_status(cls, status: DeploymentStatus) -> int:
        """
        Count deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            Number of deployments with the specified status
        """
        return sum(1 for d in cls._deployments.values() if d.status == status)
    
    @classmethod
    def filter_by_status(cls, status: DeploymentStatus) -> List['Deployment']:
        """
        Filter deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            List of deployments with the specified status
        """
        return [d for d in cls._deployments.values() if d.status == status]
    
    @classmethod
    def delete_by_id(cls, deployment_id: str) -> bool:
        """
        Delete deployment by ID
        
        Args:
            deployment_id: Deployment identifier
        
        Returns:
            True if deleted, False if not found
        """
        if deployment_id in cls._deployments:
            del cls._deployments[deployment_id]
            return True
        return False
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<Deployment {self.name} ({self.status.value})>"
