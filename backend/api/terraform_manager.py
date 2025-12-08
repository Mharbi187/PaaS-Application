"""
Terraform Manager
Handles Terraform configuration generation and execution
"""

import os
import json
import logging
from pathlib import Path
from python_terraform import Terraform, IsFlagged
from typing import Dict, Any, Optional
from flask import current_app
import uuid
from proxmoxer import ProxmoxAPI
import time
import re

logger = logging.getLogger(__name__)


class TerraformManager:
    """Manages Terraform operations for infrastructure provisioning"""
    
    def __init__(self, terraform_dir=None, state_dir=None):
        """Initialize Terraform manager"""
        if terraform_dir is None:
            from flask import current_app
            terraform_dir = Path(current_app.config['TERRAFORM_DIR'])
            state_dir = Path(current_app.config['TERRAFORM_STATE_DIR'])
        
        self.terraform_dir = Path(terraform_dir) if terraform_dir else Path('./terraform')
        self.state_dir = Path(state_dir) if state_dir else Path('./terraform/states')
        self.ssh_keys_dir = Path('./ssh_keys')
        self.ssh_keys_dir.mkdir(exist_ok=True)
        
        # Detect Terraform executable path
        terraform_exe = None
        # Check for terraform in project directory
        project_tf_bin = Path('./terraform_bin/terraform.exe')
        project_tf = Path('./terraform_1.14.0_windows_amd64/terraform.exe')
        
        if project_tf_bin.exists():
            terraform_exe = str(project_tf_bin.absolute())
        elif project_tf.exists():
            terraform_exe = str(project_tf.absolute())
        
        self.tf = Terraform(
            working_dir=str(self.terraform_dir),
            terraform_bin_path=terraform_exe
        )
    
    def _ensure_ssh_keypair(self) -> tuple[Path, Path]:
        """
        Ensure SSH keypair exists, generate if needed
        
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        private_key_path = self.ssh_keys_dir / 'id_rsa'
        public_key_path = self.ssh_keys_dir / 'id_rsa.pub'
        
        if not private_key_path.exists() or not public_key_path.exists():
            logger.info("Generating new SSH keypair")
            from paramiko import RSAKey
            
            # Generate 2048-bit RSA key
            key = RSAKey.generate(2048)
            
            # Save private key
            key.write_private_key_file(str(private_key_path))
            
            # Save public key in OpenSSH format
            with open(public_key_path, 'w') as f:
                f.write(f"ssh-rsa {key.get_base64()}")
            
            logger.info(f"SSH keypair generated: {private_key_path}")
        
        return private_key_path, public_key_path
    
    def generate_config(
        self,
        deployment_type: str,
        framework: str,
        name: str,
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Terraform configuration for deployment
        
        Args:
            deployment_type: 'vm' or 'lxc'
            framework: Framework identifier
            name: Deployment name
            resources: Resource specifications (CPU, memory, disk)
        
        Returns:
            Dictionary containing Terraform configuration
        """
        try:
            # Generate unique VM ID
            vm_id = self._generate_vm_id()
            
            # Get framework configuration
            framework_config = current_app.config['SUPPORTED_FRAMEWORKS'].get(framework)
            if not framework_config:
                raise ValueError(f"Unsupported framework: {framework}")
            
            # Sanitize name for hostname (DNS compliant: replace underscores with hyphens)
            sanitized_name = name.replace('_', '-').lower()
            
            # Ensure SSH keypair exists
            private_key_path, public_key_path = self._ensure_ssh_keypair()
            
            # Read public key
            with open(public_key_path, 'r') as f:
                ssh_public_key = f.read().strip()
            
            logger.info(f"Generated Terraform config for {name} (hostname: {sanitized_name})")
            
            # Prepare variables
            tf_vars = {
                'deployment_name': sanitized_name,  # Used as hostname in Terraform
                'vm_id': vm_id,
                'deployment_type': deployment_type,
                'framework': framework,
                'framework_language': framework_config['language'],
                'framework_port': framework_config['port'],
                
                # Proxmox settings
                'proxmox_url': current_app.config['PROXMOX_URL'],
                'proxmox_user': current_app.config['PROXMOX_USER'],
                'proxmox_password': current_app.config['PROXMOX_PASSWORD'],
                'proxmox_node': current_app.config['PROXMOX_NODE'],
                'proxmox_storage': current_app.config['PROXMOX_STORAGE'],
                'network_bridge': current_app.config['PROXMOX_NETWORK_BRIDGE'],
                
                # Resource specifications
                'cores': resources.get('cores', current_app.config['DEFAULT_VM_CORES'] if deployment_type == 'vm' else current_app.config['DEFAULT_LXC_CORES']),
                'memory': resources.get('memory', current_app.config['DEFAULT_VM_MEMORY'] if deployment_type == 'vm' else current_app.config['DEFAULT_LXC_MEMORY']),
                'disk_size': resources.get('disk', current_app.config['DEFAULT_VM_DISK'] if deployment_type == 'vm' else current_app.config['DEFAULT_LXC_DISK']),
                
                # Network settings
                'gateway': current_app.config['GATEWAY'],
                'dns_servers': ','.join(current_app.config['DNS_SERVERS']),
                
                # SSH settings
                'ssh_user': current_app.config.get('SSH_USER', 'root'),
                'ssh_public_keys': [ssh_public_key]  # Pass as list
            }
            
            # Add OS template/ISO based on deployment type
            if deployment_type == 'lxc':
                tf_vars['os_template'] = current_app.config['LXC_TEMPLATES']['ubuntu-22.04']
            else:
                # For VMs, use cloud-init template for cloning
                tf_vars['vm_template'] = current_app.config.get('VM_TEMPLATE', 'ubuntu-22-cloudinit')
                tf_vars['iso_image'] = current_app.config['VM_ISOS'].get('ubuntu-22.04', '')
            
            return {
                'variables': tf_vars,
                'deployment_type': deployment_type
            }
        
        except Exception as e:
            logger.error(f"Error generating Terraform config: {e}")
            raise
    
    def apply(self, deployment_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Terraform configuration to create infrastructure
        
        Args:
            deployment_name: Name of the deployment
            config: Terraform configuration
        
        Returns:
            Dictionary with success status and deployment details
        """
        try:
            logger.info(f"Applying Terraform for {deployment_name}")
            
            # Create state directory for this deployment
            deployment_state_dir = self.state_dir / deployment_name
            deployment_state_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Terraform
            return_code, stdout, stderr = self.tf.init(
                capture_output=True
            )
            
            if return_code != 0:
                raise Exception(f"Terraform init failed: {stderr}")
            
            # Create or select workspace for this deployment
            # Check if workspace exists
            return_code, stdout, stderr = self.tf.cmd('workspace', 'list', capture_output=True)
            workspace_exists = deployment_name in (stdout.decode() if isinstance(stdout, bytes) else stdout)
            
            if not workspace_exists:
                # Create new workspace
                logger.info(f"Creating Terraform workspace: {deployment_name}")
                return_code, stdout, stderr = self.tf.cmd('workspace', 'new', deployment_name, capture_output=True)
                if return_code != 0:
                    raise Exception(f"Failed to create workspace: {stderr}")
            else:
                # Select existing workspace
                logger.info(f"Selecting Terraform workspace: {deployment_name}")
                return_code, stdout, stderr = self.tf.cmd('workspace', 'select', deployment_name, capture_output=True)
                if return_code != 0:
                    raise Exception(f"Failed to select workspace: {stderr}")
            
            # Prepare variables file
            var_file = deployment_state_dir / 'terraform.tfvars.json'
            with open(var_file, 'w') as f:
                json.dump(config['variables'], f, indent=2)
            
            # Convert to relative path from terraform directory
            relative_var_file = var_file.relative_to(self.terraform_dir).as_posix()
            
            # Plan
            return_code, stdout, stderr = self.tf.plan(
                var_file=relative_var_file,
                capture_output=True
            )
            
            # Terraform plan returns 0 for no changes, 2 for changes planned, 1 for error
            if return_code == 1:
                error_msg = stderr.decode() if isinstance(stderr, bytes) else stderr
                stdout_msg = stdout.decode() if isinstance(stdout, bytes) else stdout
                logger.error(f"Terraform plan failed. Return code: {return_code}")
                logger.error(f"STDOUT: {stdout_msg}")
                logger.error(f"STDERR: {error_msg}")
                raise Exception(f"Terraform plan failed: {error_msg}\nOutput: {stdout_msg}")
            
            logger.info(f"Terraform plan succeeded. Resources to {'add' if return_code == 2 else 'maintain'}")
            
            # Apply
            return_code, stdout, stderr = self.tf.apply(
                var_file=relative_var_file,
                skip_plan=True,
                capture_output=True
            )
            
            if return_code != 0:
                error_msg = stderr.decode() if isinstance(stderr, bytes) else stderr
                stdout_msg = stdout.decode() if isinstance(stdout, bytes) else stdout
                logger.error(f"Terraform apply failed. Return code: {return_code}")
                logger.error(f"STDOUT: {stdout_msg}")
                logger.error(f"STDERR: {error_msg}")
                raise Exception(f"Terraform apply failed: {error_msg}\nOutput: {stdout_msg}")
            
            # Get outputs
            outputs = self.tf.output(json=IsFlagged)
            
            vm_id = outputs.get('vm_id', {}).get('value')
            ip_address = outputs.get('ip_address', {}).get('value')
            
            # If IP is not resolved (for LXC with DHCP), get it from Proxmox
            if ip_address in ['Check Proxmox Console', 'pending', None]:
                logger.info(f"IP not in outputs, fetching from Proxmox for VM/LXC ID {vm_id}")
                ip_address = self._get_ip_from_proxmox(vm_id, config['deployment_type'])
            
            logger.info(f"Terraform applied successfully for {deployment_name}. IP: {ip_address}")
            
            return {
                'success': True,
                'ip_address': ip_address,
                'vm_id': vm_id,
                'outputs': outputs
            }
        
        except Exception as e:
            logger.error(f"Error applying Terraform: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def destroy(self, deployment_name: str) -> Dict[str, Any]:
        """
        Destroy infrastructure for a deployment
        
        Args:
            deployment_name: Name of the deployment to destroy
        
        Returns:
            Dictionary with success status
        """
        try:
            logger.info(f"Destroying infrastructure for {deployment_name}")
            
            deployment_state_dir = self.state_dir / deployment_name
            var_file = deployment_state_dir / 'terraform.tfvars.json'
            
            if not var_file.exists():
                raise Exception(f"No Terraform state found for {deployment_name}")
            
            # Select the workspace for this deployment
            logger.info(f"Selecting Terraform workspace: {deployment_name}")
            return_code, stdout, stderr = self.tf.cmd('workspace', 'select', deployment_name, capture_output=True)
            if return_code != 0:
                raise Exception(f"Failed to select workspace: {stderr}")
            
            # Convert to relative path
            relative_var_file = var_file.relative_to(self.terraform_dir).as_posix()
            
            # Destroy
            return_code, stdout, stderr = self.tf.destroy(
                var_file=relative_var_file,
                auto_approve=True,
                capture_output=True
            )
            
            if return_code != 0:
                raise Exception(f"Terraform destroy failed: {stderr}")
            
            logger.info(f"Infrastructure destroyed for {deployment_name}")
            
            # Switch back to default workspace
            self.tf.cmd('workspace', 'select', 'default', capture_output=True)
            
            # Delete the workspace
            logger.info(f"Deleting Terraform workspace: {deployment_name}")
            self.tf.cmd('workspace', 'delete', deployment_name, capture_output=True)
            
            # Clean up state directory
            import shutil
            shutil.rmtree(deployment_state_dir)
            
            return {
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error destroying infrastructure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def deploy_application(
        self,
        ip_address: str,
        framework: str,
        github_url: str,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Deploy application on provisioned infrastructure via SSH
        
        Args:
            ip_address: IP address of the VM/LXC
            framework: Framework identifier
            github_url: GitHub repository URL
            env_vars: Optional environment variables for the application
        
        Returns:
            Dictionary with success status
        """
        try:
            logger.info(f"Deploying application from {github_url} on {ip_address}")
            
            import paramiko
            import time
            
            # Get framework config
            framework_config = current_app.config['SUPPORTED_FRAMEWORKS'].get(framework)
            if not framework_config:
                raise ValueError(f"Unsupported framework: {framework}")
            
            # SSH credentials - use key-based auth
            ssh_user = current_app.config.get('SSH_USER', 'root')
            private_key_path, _ = self._ensure_ssh_keypair()
            
            # Wait for SSH to be ready
            logger.info(f"Waiting for SSH to be ready on {ip_address}")
            max_retries = 30
            for i in range(max_retries):
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    # Use private key for authentication
                    ssh.connect(
                        ip_address, 
                        username=ssh_user, 
                        key_filename=str(private_key_path),
                        timeout=10,
                        look_for_keys=False,
                        allow_agent=False
                    )
                    logger.info(f"SSH connection established to {ip_address}")
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"SSH connection failed after {max_retries} attempts: {e}")
                    time.sleep(10)
            
            # Build deployment commands based on framework
            commands = self._build_deployment_commands(framework, framework_config, github_url, env_vars)
            
            # Execute commands
            for idx, cmd in enumerate(commands):
                logger.info(f"Executing command {idx+1}/{len(commands)}: {cmd[:100]}...")
                stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
                exit_status = stdout.channel.recv_exit_status()
                
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if exit_status != 0:
                    logger.error(f"Command failed with exit code {exit_status}: {error}")
                    raise Exception(f"Deployment command failed: {error}")
                
                logger.info(f"Command output: {output[:200]}...")
            
            ssh.close()
            logger.info(f"Application deployed successfully on {ip_address}")
            
            return {
                'success': True,
                'message': 'Application deployed successfully',
                'access_url': f"http://{ip_address}:{framework_config['port']}"
            }
        
        except Exception as e:
            logger.error(f"Error deploying application: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_deployment_commands(
        self,
        framework: str,
        framework_config: Dict[str, Any],
        github_url: str,
        env_vars: Optional[Dict[str, str]] = None
    ) -> list:
        """Build deployment commands based on framework type"""
        
        language = framework_config['language']
        port = framework_config['port']
        commands = []
        
        # Helper to wait for apt lock
        wait_for_lock = "while fuser /var/lib/dpkg/lock >/dev/null 2>&1 || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do echo 'Waiting for lock...'; sleep 1; done;"
        
        # Base setup - Chain commands to persist environment and ensure sequential execution
        base_cmd = f"export DEBIAN_FRONTEND=noninteractive && {wait_for_lock} apt-get update && {wait_for_lock} apt-get install -y apt-utils git curl build-essential"
        commands.append(base_cmd)
        
        # Language-specific installation
        if language == 'nodejs':
            node_cmd = (
                f"export DEBIAN_FRONTEND=noninteractive && {wait_for_lock} "
                "curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && "
                f"{wait_for_lock} apt-get install -y nodejs"
            )
            commands.append(node_cmd)
            
        elif language == 'python':
            py_cmd = f"export DEBIAN_FRONTEND=noninteractive && {wait_for_lock} apt-get install -y python3 python3-pip"
            commands.append(py_cmd)
            
        elif language == 'php':
            php_cmd = f"export DEBIAN_FRONTEND=noninteractive && {wait_for_lock} apt-get install -y php php-cli php-fpm php-mysql composer"
            commands.append(php_cmd)
        
        # Application setup
        # Clean up previous app dir if exists
        commands.append('rm -rf /opt/app')
        
        # Clone repository
        commands.append(f'git clone {github_url} /opt/app')
        
        # Create .env file if env_vars provided
        if env_vars:
            env_content = '\\n'.join([f'{k}={v}' for k, v in env_vars.items()])
            commands.append(f'cat > /opt/app/.env << EOF\\n{env_content}\\nEOF')
        
        # Install dependencies and start based on framework
        start_script = ""
        
        if framework == 'react':
            start_script = (
                "cd /opt/app && npm install && npm run build && "
                "npm install -g serve && "
                "nohup serve -s build -l 3000 > /var/log/app.log 2>&1 &"
            )
        elif framework in ['express', 'nextjs']:
            start_script = (
                "cd /opt/app && npm install && "
                "nohup npm start > /var/log/app.log 2>&1 &"
            )
        elif framework == 'django':
            start_script = (
                "cd /opt/app && pip3 install -r requirements.txt && "
                "nohup python3 manage.py runserver 0.0.0.0:8000 > /var/log/app.log 2>&1 &"
            )
        elif framework == 'flask':
            start_script = (
                "cd /opt/app && pip3 install -r requirements.txt && "
                "nohup python3 app.py > /var/log/app.log 2>&1 &"
            )
        elif framework == 'laravel':
            start_script = (
                "cd /opt/app && composer install && "
                "php artisan key:generate && "
                "nohup php artisan serve --host=0.0.0.0 --port=8000 > /var/log/app.log 2>&1 &"
            )
        else:
            # Generic Node.js app
            start_script = (
                "cd /opt/app && npm install && "
                "nohup npm start > /var/log/app.log 2>&1 &"
            )
            
        commands.append(start_script)
        
        return commands
    
    def get_logs(self, deployment_name: str) -> str:
        """
        Get Terraform logs for a deployment
        
        Args:
            deployment_name: Name of the deployment
        
        Returns:
            Log content as string
        """
        try:
            log_file = self.state_dir / deployment_name / 'terraform.log'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    return f.read()
            return "No logs available"
        
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return f"Error reading logs: {str(e)}"
    
    def _get_ip_from_proxmox(self, vm_id: str, deployment_type: str, max_retries: int = 10) -> str:
        """
        Get IP address from Proxmox API for a VM or LXC container
        
        Args:
            vm_id: VM or LXC container ID
            deployment_type: 'vm' or 'lxc'
            max_retries: Maximum number of retry attempts
        
        Returns:
            IP address as string
        """
        try:
            # Parse Proxmox URL to extract host
            proxmox_url = current_app.config['PROXMOX_URL']
            # Extract host from URL like https://192.168.100.2:8006/api2/json
            import re
            host_match = re.search(r'https?://([^:/]+)', proxmox_url)
            if not host_match:
                raise ValueError(f"Invalid Proxmox URL: {proxmox_url}")
            proxmox_host = host_match.group(1)
            
            # Connect to Proxmox API
            proxmox = ProxmoxAPI(
                proxmox_host,
                user=current_app.config['PROXMOX_USER'],
                password=current_app.config['PROXMOX_PASSWORD'],
                verify_ssl=False
            )
            
            node = current_app.config['PROXMOX_NODE']
            
            # Retry getting IP address (may take a moment after container creation)
            for attempt in range(max_retries):
                try:
                    if deployment_type == 'lxc':
                        # Get LXC network interfaces
                        interfaces = proxmox.nodes(node).lxc(vm_id).interfaces.get()
                        
                        # Ensure interfaces is a list
                        if not interfaces:
                            if attempt < max_retries - 1:
                                time.sleep(3)
                            continue

                        # Look for eth0 with inet address
                        for interface in interfaces:
                            if interface.get('name') == 'eth0' and 'inet' in interface:
                                ip = interface['inet'].split('/')[0]  # Remove CIDR notation
                                if ip and ip != '0.0.0.0':
                                    logger.info(f"Found LXC IP: {ip} for container {vm_id}")
                                    return ip
                    else:
                        # Get VM network interfaces (for QEMU VMs)
                        try:
                            agent_info = proxmox.nodes(node).qemu(vm_id).agent.get('network-get-interfaces')
                        except Exception:
                            # Agent might not be running yet
                            agent_info = None

                        if not agent_info or not agent_info.get('result'):
                            if attempt < max_retries - 1:
                                time.sleep(3)
                            continue

                        interfaces = agent_info.get('result', [])
                        
                        # Look for network interface with IP
                        for iface in interfaces:
                            if iface.get('name') in ['eth0', 'ens18']:
                                for ip_addr in iface.get('ip-addresses', []):
                                    if ip_addr.get('ip-address-type') == 'ipv4':
                                        ip = ip_addr.get('ip-address')
                                        if ip and not ip.startswith('127.'):
                                            logger.info(f"Found VM IP: {ip} for VM {vm_id}")
                                            return ip
                    
                    # If no IP found, wait and retry
                    if attempt < max_retries - 1:
                        logger.info(f"IP not ready yet for {deployment_type} {vm_id}, retry {attempt + 1}/{max_retries}")
                        time.sleep(3)
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Error getting IP (attempt {attempt + 1}): {e}")
                        time.sleep(3)
                    else:
                        raise
            
            raise Exception(f"Could not retrieve IP address for {deployment_type} {vm_id} after {max_retries} attempts")
        
        except Exception as e:
            logger.error(f"Error getting IP from Proxmox: {e}")
            raise
    
    @staticmethod
    def _generate_vm_id() -> int:
        """
        Generate a unique VM ID
        
        Returns:
            Unique VM ID (100-999 range for safety)
        """
        # In production, this should check existing VMs in Proxmox
        # For now, generate a random ID
        import random
        return random.randint(100, 999)
