"""
Deployment Model
Represents a deployment in the PaaS platform using SQLAlchemy ORM
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import json
from backend.extensions import db


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = 'pending'
    PROVISIONING = 'provisioning'
    DEPLOYING = 'deploying'
    RUNNING = 'running'
    FAILED = 'failed'
    STOPPED = 'stopped'
    DELETED = 'deleted'


class Deployment(db.Model):
    """Deployment model class using SQLAlchemy"""
    
    __tablename__ = 'deployments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, index=True)
    deployment_type = db.Column(db.String(10), nullable=False)  # 'vm' or 'lxc'
    framework = db.Column(db.String(50), nullable=False)
    github_url = db.Column(db.String(500), nullable=False)
    resources_json = db.Column(db.Text, nullable=True)  # JSON string for resources
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    vm_id = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
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
        if id:
            self.id = id
        self.name = name
        self.deployment_type = deployment_type
        self.framework = framework
        self.github_url = github_url
        self.resources = resources  # Uses property setter
        self.status = status  # Uses property setter
        self.created_at = created_at
    
    @property
    def resources(self) -> Dict[str, Any]:
        """Get resources as dictionary"""
        if self.resources_json:
            return json.loads(self.resources_json)
        return {}
    
    @resources.setter
    def resources(self, value: Dict[str, Any]):
        """Set resources from dictionary"""
        self.resources_json = json.dumps(value) if value else None
    
    @property
    def status(self) -> DeploymentStatus:
        """Get status as enum"""
        return DeploymentStatus(self._status) if self._status else DeploymentStatus.PENDING
    
    @status.setter
    def status(self, value):
        """Set status from enum or string"""
        if isinstance(value, DeploymentStatus):
            self._status = value.value
        else:
            self._status = value
    
    # Override the status column to use _status internally
    _status = db.Column('status', db.String(20), nullable=False, default='pending')
    
    def save(self):
        """Save the deployment to database"""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete the deployment from database"""
        db.session.delete(self)
        db.session.commit()
    
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
            'status': self.status.value if isinstance(self.status, DeploymentStatus) else self.status,
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
        return cls.query.get(deployment_id)
    
    @classmethod
    def get_all(cls) -> List['Deployment']:
        """
        Get all deployments
        
        Returns:
            List of all deployments
        """
        return cls.query.all()
    
    @classmethod
    def count_all(cls) -> int:
        """
        Count all deployments
        
        Returns:
            Total number of deployments
        """
        return cls.query.count()
    
    @classmethod
    def count_by_status(cls, status: DeploymentStatus) -> int:
        """
        Count deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            Number of deployments with the specified status
        """
        status_value = status.value if isinstance(status, DeploymentStatus) else status
        return cls.query.filter_by(_status=status_value).count()
    
    @classmethod
    def filter_by_status(cls, status: DeploymentStatus) -> List['Deployment']:
        """
        Filter deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            List of deployments with the specified status
        """
        status_value = status.value if isinstance(status, DeploymentStatus) else status
        return cls.query.filter_by(_status=status_value).all()
    
    @classmethod
    def delete_by_id(cls, deployment_id: str) -> bool:
        """
        Delete deployment by ID
        
        Args:
            deployment_id: Deployment identifier
        
        Returns:
            True if deleted, False if not found
        """
        deployment = cls.query.get(deployment_id)
        if deployment:
            db.session.delete(deployment)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def get_used_vm_ids(cls) -> List[int]:
        """
        Get all VM IDs currently in use
        
        Returns:
            List of VM IDs
        """
        result = cls.query.with_entities(cls.vm_id).filter(
            cls.vm_id.isnot(None),
            cls._status != 'deleted'
        ).all()
        return [r[0] for r in result if r[0] is not None]
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<Deployment {self.name} ({self._status})>"
