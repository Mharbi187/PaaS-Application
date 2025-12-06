"""
Deployment Model - SQLAlchemy ORM
Represents a deployment in the PaaS platform
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
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
    """Deployment model class - SQLAlchemy ORM"""
    
    __tablename__ = 'deployments'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    deployment_type = db.Column(db.String(50), nullable=False)  # 'vm' or 'lxc'
    framework = db.Column(db.String(100), nullable=False)
    github_url = db.Column(db.String(500), nullable=False)
    
    # Resources as JSON
    resources = db.Column(db.JSON, nullable=True)
    
    # Status tracking
    status = db.Column(
        db.String(50),
        nullable=False,
        default=DeploymentStatus.PENDING.value,
        index=True
    )
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    deployed_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Infrastructure details
    ip_address = db.Column(db.String(50), nullable=True)
    vm_id = db.Column(db.Integer, nullable=True, unique=True)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    user_id = db.Column(db.String(100), nullable=True)  # For future multi-user support
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    
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
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'ip_address': self.ip_address,
            'vm_id': self.vm_id,
            'error_message': self.error_message,
            'tags': self.tags
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
    def get_by_name(cls, name: str) -> Optional['Deployment']:
        """
        Get deployment by name
        
        Args:
            name: Deployment name
        
        Returns:
            Deployment instance or None
        """
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_all(cls) -> List['Deployment']:
        """
        Get all deployments
        
        Returns:
            List of deployments
        """
        return cls.query.all()
    
    @classmethod
    def get_by_status(cls, status: DeploymentStatus) -> List['Deployment']:
        """
        Get deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            List of deployments
        """
        return cls.query.filter_by(status=status.value).all()
    
    @classmethod
    def count_all(cls) -> int:
        """
        Count total deployments
        
        Returns:
            Total count
        """
        return cls.query.count()
    
    @classmethod
    def count_by_status(cls, status: DeploymentStatus) -> int:
        """
        Count deployments by status
        
        Args:
            status: Deployment status
        
        Returns:
            Count
        """
        return cls.query.filter_by(status=status.value).count()
    
    @classmethod
    def get_recent(cls, limit: int = 10) -> List['Deployment']:
        """
        Get recent deployments
        
        Args:
            limit: Number of deployments to retrieve
        
        Returns:
            List of recent deployments
        """
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
    
    def save(self) -> None:
        """Save deployment to database"""
        db.session.add(self)
        db.session.commit()
    
    def update(self) -> None:
        """Update deployment in database"""
        db.session.commit()
    
    def delete(self) -> None:
        """Delete deployment from database"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self) -> str:
        return f"<Deployment {self.name} ({self.status})>"
