"""
Helper Utilities
General utility functions for the PaaS platform
"""

import logging
from pathlib import Path
from typing import Any, Dict
import json


def setup_logging(log_file: Path, log_level: str = 'INFO'):
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {log_level}, File: {log_file}")


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string
    
    Args:
        bytes_value: Number of bytes
    
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_memory(mb_value: int) -> str:
    """
    Format memory in MB to human-readable string
    
    Args:
        mb_value: Memory in MB
    
    Returns:
        Formatted string (e.g., "2 GB")
    """
    if mb_value < 1024:
        return f"{mb_value} MB"
    gb_value = mb_value / 1024
    return f"{gb_value:.1f} GB"


def parse_github_url(url: str) -> Dict[str, str]:
    """
    Parse GitHub URL to extract owner and repository
    
    Args:
        url: GitHub repository URL
    
    Returns:
        Dictionary with 'owner' and 'repo' keys
    """
    # Remove trailing slashes and .git
    url = url.rstrip('/').rstrip('.git')
    
    # Extract parts
    parts = url.split('/')
    
    if len(parts) >= 2:
        return {
            'owner': parts[-2],
            'repo': parts[-1]
        }
    
    return {'owner': '', 'repo': ''}


def generate_deployment_config(
    deployment_type: str,
    framework: str,
    name: str,
    resources: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate deployment configuration
    
    Args:
        deployment_type: 'vm' or 'lxc'
        framework: Framework identifier
        name: Deployment name
        resources: Resource specifications
    
    Returns:
        Complete deployment configuration
    """
    config = {
        'deployment': {
            'name': name,
            'type': deployment_type,
            'framework': framework
        },
        'resources': resources,
        'metadata': {
            'created_by': 'paas-platform',
            'version': '1.0.0'
        }
    }
    
    return config


def save_json(filepath: Path, data: Dict[str, Any]) -> None:
    """
    Save data to JSON file
    
    Args:
        filepath: Path to JSON file
        data: Data to save
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filepath: Path) -> Dict[str, Any]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        Loaded data
    """
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r') as f:
        return json.load(f)


def sanitize_name(name: str) -> str:
    """
    Sanitize deployment name for use in file paths and identifiers
    
    Args:
        name: Original name
    
    Returns:
        Sanitized name
    """
    # Replace spaces with hyphens
    name = name.replace(' ', '-')
    
    # Remove non-alphanumeric characters except hyphens and underscores
    import re
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    return name


def get_framework_info(framework: str, supported_frameworks: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get framework information
    
    Args:
        framework: Framework identifier
        supported_frameworks: Dictionary of supported frameworks
    
    Returns:
        Framework information or empty dict if not found
    """
    return supported_frameworks.get(framework, {})


def is_port_available(port: int) -> bool:
    """
    Check if a port is available
    
    Args:
        port: Port number
    
    Returns:
        True if available, False otherwise
    """
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False


def calculate_deployment_cost(resources: Dict[str, Any]) -> float:
    """
    Calculate estimated cost for deployment (for internal tracking)
    
    Args:
        resources: Resource specifications
    
    Returns:
        Estimated cost per month (arbitrary units)
    """
    cores = resources.get('cores', 1)
    memory = resources.get('memory', 1024)  # MB
    disk = resources.get('disk', 10)  # GB
    
    # Simple cost calculation (can be customized)
    cost = (cores * 10) + (memory / 1024 * 5) + (disk * 0.5)
    
    return round(cost, 2)
