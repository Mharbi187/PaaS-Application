"""
Configuration module for PaaS Platform
Loads environment variables and provides configuration settings
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Check if .env exists, if not create from example
env_path = Path('.env')
if not env_path.exists():
    env_example = Path('.env.example')
    if env_example.exists():
        print("⚠️  .env file not found. Creating from .env.example...")
        import shutil
        shutil.copy(env_example, env_path)
        print("✅ .env created. Please configure it with your settings.")
    else:
        print("❌ Neither .env nor .env.example found!")
        print("   Please create a .env file with required configuration.")

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Demo Mode
    DEMO_MODE = os.getenv('DEMO_MODE', 'True').lower() == 'true'
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Application Settings
    APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.getenv('APP_PORT', 5000))
    MAX_DEPLOYMENTS = int(os.getenv('MAX_DEPLOYMENTS', 10))
    
    # Proxmox Configuration
    PROXMOX_URL = os.getenv('PROXMOX_URL', 'https://192.168.1.100:8006/api2/json')
    PROXMOX_USER = os.getenv('PROXMOX_USER', 'root@pam')
    PROXMOX_PASSWORD = os.getenv('PROXMOX_PASSWORD', '')
    PROXMOX_NODE = os.getenv('PROXMOX_NODE', 'pve')
    PROXMOX_STORAGE = os.getenv('PROXMOX_STORAGE', 'local-lvm')
    PROXMOX_NETWORK_BRIDGE = os.getenv('PROXMOX_NETWORK_BRIDGE', 'vmbr0')
    
    # SSH Configuration for VMs/LXC
    SSH_USER = os.getenv('SSH_USER', 'root')
    SSH_PASSWORD = os.getenv('SSH_PASSWORD', '')
    SSH_PUBLIC_KEY = os.getenv('SSH_PUBLIC_KEY', '')
    
    # SSH Jump Host (Proxmox as proxy) - enables deployments from any network
    # Set SSH_JUMP_HOST to route SSH through Proxmox to reach VMs/LXC
    SSH_JUMP_HOST = os.getenv('SSH_JUMP_HOST', '')  # e.g., 192.168.126.50 or empty to disable
    SSH_JUMP_USER = os.getenv('SSH_JUMP_USER', 'root')
    SSH_JUMP_PASSWORD = os.getenv('SSH_JUMP_PASSWORD', '')
    
    # VM/LXC Templates
    VM_TEMPLATE = os.getenv('VM_TEMPLATE', 'ubuntu-22-cloudinit')
    LXC_OS_TEMPLATE = os.getenv('LXC_OS_TEMPLATE', 'debian-12-standard')
    
    # Terraform Settings
    TERRAFORM_DIR = Path(os.getenv('TERRAFORM_DIR', './terraform'))
    TERRAFORM_STATE_DIR = Path(os.getenv('TERRAFORM_STATE_DIR', './terraform/states'))
    
    # Default VM Settings
    DEFAULT_VM_MEMORY = int(os.getenv('DEFAULT_VM_MEMORY', 2048))
    DEFAULT_VM_CORES = int(os.getenv('DEFAULT_VM_CORES', 2))
    DEFAULT_VM_DISK = int(os.getenv('DEFAULT_VM_DISK', 20))
    
    # Default LXC Settings
    DEFAULT_LXC_MEMORY = int(os.getenv('DEFAULT_LXC_MEMORY', 1024))
    DEFAULT_LXC_CORES = int(os.getenv('DEFAULT_LXC_CORES', 1))
    DEFAULT_LXC_DISK = int(os.getenv('DEFAULT_LXC_DISK', 10))
    
    # GitHub Settings
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///deployments.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv('LOG_FILE', './logs/paas.log'))
    
    # Network Settings
    SUBNET = os.getenv('SUBNET', '192.168.100.0/24')
    GATEWAY = os.getenv('GATEWAY', '192.168.100.1')
    DNS_SERVERS = os.getenv('DNS_SERVERS', '8.8.8.8,8.8.4.4').split(',')
    
    # Supported Frameworks
    SUPPORTED_FRAMEWORKS = {
        'django': {
            'name': 'Django',
            'language': 'python',
            'version': '4.2',
            'port': 8000,
            'install_cmd': 'pip install django gunicorn'
        },
        'laravel': {
            'name': 'Laravel',
            'language': 'php',
            'version': '10.x',
            'port': 8000,
            'install_cmd': 'composer global require laravel/installer'
        },
        'express': {
            'name': 'Express.js',
            'language': 'nodejs',
            'version': '18.x',
            'port': 3000,
            'install_cmd': 'npm install express'
        },
        'flask': {
            'name': 'Flask',
            'language': 'python',
            'version': '3.0',
            'port': 5000,
            'install_cmd': 'pip install flask gunicorn'
        },
        'fastapi': {
            'name': 'FastAPI',
            'language': 'python',
            'version': '0.104',
            'port': 8000,
            'install_cmd': 'pip install fastapi uvicorn'
        },
        'react': {
            'name': 'React',
            'language': 'nodejs',
            'version': '18.x',
            'port': 3000,
            'install_cmd': 'npx create-react-app'
        },
        'vuejs': {
            'name': 'Vue.js',
            'language': 'nodejs',
            'version': '3.x',
            'port': 8080,
            'install_cmd': 'npm install -g @vue/cli'
        },
        'nextjs': {
            'name': 'Next.js',
            'language': 'nodejs',
            'version': '14.x',
            'port': 3000,
            'install_cmd': 'npx create-next-app@latest'
        }
    }
    
    # OS Templates for LXC
    LXC_TEMPLATES = {
        'ubuntu-22.04': os.getenv('LXC_OS_TEMPLATE', 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst'),
        'ubuntu-20.04': 'ubuntu-20.04-standard',
        'debian-12': 'debian-12-standard',
        'debian-11': 'debian-11-standard',
        'alpine-3.18': 'alpine-3.18-default'
    }
    
    # VM ISO Images
    VM_ISOS = {
        'ubuntu-22.04': 'ubuntu-22.04-server-amd64.iso',
        'ubuntu-20.04': 'ubuntu-20.04-server-amd64.iso',
        'debian-12': 'debian-12-netinst.iso',
        'debian-11': 'debian-11-netinst.iso'
    }
    
    @staticmethod
    def init_app():
        """Initialize application directories"""
        # Create necessary directories
        Config.TERRAFORM_STATE_DIR.mkdir(parents=True, exist_ok=True)
        Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate Proxmox credentials
        if not Config.PROXMOX_PASSWORD:
            raise ValueError("PROXMOX_PASSWORD must be set in environment variables")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    @staticmethod
    def init_app():
        """Initialize production app with additional security checks"""
        Config.init_app()
        
        # Enforce SECRET_KEY in production
        secret_key = os.getenv('SECRET_KEY', '')
        if not secret_key or secret_key == 'dev-secret-key-change-in-production':
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
