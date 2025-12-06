"""
Validators
Input validation for deployment requests
"""

import re
from typing import Dict, Any, Tuple, List
from flask import current_app
import validators as val


def validate_deployment_request(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate deployment request data
    
    Args:
        data: Request data dictionary
    
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []
    
    # Check required fields
    required_fields = ['deployment_type', 'framework', 'github_url', 'name']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate deployment type
    deployment_type = data.get('deployment_type')
    if deployment_type not in ['vm', 'lxc']:
        errors.append("Invalid deployment_type. Must be 'vm' or 'lxc'")
    
    # Validate framework
    framework = data.get('framework')
    supported_frameworks = current_app.config.get('SUPPORTED_FRAMEWORKS', {})
    if framework not in supported_frameworks:
        errors.append(f"Unsupported framework: {framework}")
    
    # Validate GitHub URL
    github_url = data.get('github_url')
    if not validate_github_url(github_url):
        errors.append("Invalid GitHub URL. Must be a valid GitHub repository URL")
    
    # Validate deployment name
    name = data.get('name')
    if not validate_deployment_name(name):
        errors.append("Invalid deployment name. Must be alphanumeric with hyphens/underscores, 3-50 characters")
    
    # Validate resources if provided
    resources = data.get('resources', {})
    if resources:
        resource_errors = validate_resources(resources, deployment_type)
        errors.extend(resource_errors)
    
    return len(errors) == 0, errors


def validate_github_url(url: str) -> bool:
    """
    Validate GitHub repository URL
    
    Args:
        url: GitHub repository URL
    
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    # Check if it's a valid URL
    if not val.url(url):
        return False
    
    # Check if it's a GitHub URL
    github_pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    return bool(re.match(github_pattern, url))


def validate_deployment_name(name: str) -> bool:
    """
    Validate deployment name
    
    Args:
        name: Deployment name
    
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Must be alphanumeric with hyphens/underscores, 3-50 characters
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, name))


def validate_resources(resources: Dict[str, Any], deployment_type: str) -> List[str]:
    """
    Validate resource specifications
    
    Args:
        resources: Resource specifications (cores, memory, disk)
        deployment_type: 'vm' or 'lxc'
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Define limits based on deployment type
    if deployment_type == 'vm':
        limits = {
            'cores': {'min': 1, 'max': 16},
            'memory': {'min': 512, 'max': 32768},  # MB
            'disk': {'min': 10, 'max': 500}  # GB
        }
    else:  # lxc
        limits = {
            'cores': {'min': 1, 'max': 8},
            'memory': {'min': 256, 'max': 16384},  # MB
            'disk': {'min': 5, 'max': 200}  # GB
        }
    
    # Validate cores
    cores = resources.get('cores')
    if cores is not None:
        if not isinstance(cores, int):
            errors.append("Cores must be an integer")
        elif cores < limits['cores']['min'] or cores > limits['cores']['max']:
            errors.append(f"Cores must be between {limits['cores']['min']} and {limits['cores']['max']}")
    
    # Validate memory
    memory = resources.get('memory')
    if memory is not None:
        if not isinstance(memory, int):
            errors.append("Memory must be an integer (in MB)")
        elif memory < limits['memory']['min'] or memory > limits['memory']['max']:
            errors.append(f"Memory must be between {limits['memory']['min']} and {limits['memory']['max']} MB")
    
    # Validate disk
    disk = resources.get('disk')
    if disk is not None:
        if not isinstance(disk, int):
            errors.append("Disk must be an integer (in GB)")
        elif disk < limits['disk']['min'] or disk > limits['disk']['max']:
            errors.append(f"Disk must be between {limits['disk']['min']} and {limits['disk']['max']} GB")
    
    return errors


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address
    
    Args:
        ip: IP address string
    
    Returns:
        True if valid, False otherwise
    """
    if not ip:
        return False
    
    return val.ipv4(ip) or val.ipv6(ip)
