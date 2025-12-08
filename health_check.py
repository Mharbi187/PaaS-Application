#!/usr/bin/env python3
"""
PaaS Application Health Check Script
Validates configuration and dependencies before starting
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        if Path('.env.example').exists():
            print("   Creating .env from .env.example...")
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env created. Please configure it.")
            return False
        return False
    
    # Check required variables
    required_vars = [
        'PROXMOX_URL',
        'PROXMOX_USER',
        'PROXMOX_PASSWORD',
        'PROXMOX_NODE'
    ]
    
    with open(env_path) as f:
        env_content = f.read()
    
    missing = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=" in env_content and "=" + os.linesep in env_content:
            missing.append(var)
    
    if missing:
        print(f"⚠️  Missing or empty variables in .env: {', '.join(missing)}")
        return False
    
    print("✅ .env file configured")
    return True

def check_directories():
    """Create required directories if they don't exist"""
    dirs = ['logs', 'ssh_keys', 'terraform/states', 'instance']
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Required directories exist")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import flask
        import paramiko
        from proxmoxer import ProxmoxAPI
        from python_terraform import Terraform
        print("✅ All required packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e.name}")
        print("   Run: pip install -r requirements.txt")
        return False

def check_terraform():
    """Check if Terraform binary exists"""
    terraform_paths = [
        Path('terraform_bin/terraform.exe'),
        Path('terraform_1.14.0_windows_amd64/terraform.exe')
    ]
    
    for tf_path in terraform_paths:
        if tf_path.exists():
            print(f"✅ Terraform found at {tf_path}")
            return True
    
    print("⚠️  Terraform binary not found in expected locations")
    print("   Download from: https://www.terraform.io/downloads.html")
    return False

def main():
    print("=" * 50)
    print("PaaS Application Health Check")
    print("=" * 50)
    print()
    
    checks = [
        check_env_file(),
        check_directories(),
        check_dependencies(),
        check_terraform()
    ]
    
    print()
    if all(checks):
        print("✅ All checks passed! Application is ready to start.")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
