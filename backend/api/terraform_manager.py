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
                
                # Check for "VM not found" error which indicates state drift
                if "vm" in error_msg and "not found" in error_msg:
                    logger.warning(f"State drift detected (VM not found). Attempting to clean state for {deployment_name}")
                    
                    # Try to remove the resource from state
                    resource_addr = "proxmox_lxc.deployment_lxc[0]" if config['deployment_type'] == 'lxc' else "proxmox_vm_qemu.deployment_vm[0]"
                    
                    logger.info(f"Removing {resource_addr} from state...")
                    self.tf.cmd('state', 'rm', resource_addr, capture_output=True)
                    
                    # Retry plan
                    logger.info("Retrying Terraform plan...")
                    return_code, stdout, stderr = self.tf.plan(
                        var_file=relative_var_file,
                        capture_output=True
                    )
                    
                    if return_code == 1:
                        # If still failing, raise error
                        error_msg = stderr.decode() if isinstance(stderr, bytes) else stderr
                        stdout_msg = stdout.decode() if isinstance(stdout, bytes) else stdout
                        logger.error(f"Terraform retry plan failed: {error_msg}")
                        raise Exception(f"Terraform plan failed after retry: {error_msg}\nOutput: {stdout_msg}")
                else:
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
            # Check for various "pending" states from Terraform output
            if ip_address in ['Check Proxmox Console', 'pending', 'Pending (Check Dashboard)', None] or not ip_address:
                logger.info(f"IP not in outputs (value: {ip_address}), fetching from Proxmox for VM/LXC ID {vm_id}")
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
            
            # Destroy using direct command to ensure -auto-approve is used (not deprecated -force)
            return_code, stdout, stderr = self.tf.cmd(
                'destroy',
                f'-var-file={relative_var_file}',
                '-auto-approve',
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
        
        Supports SSH jump host (routing through Proxmox) for cross-network deployments.
        
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
            
            # Check if jump host is configured
            jump_host = current_app.config.get('SSH_JUMP_HOST', '')
            
            # Wait for SSH to be ready
            logger.info(f"Waiting for SSH to be ready on {ip_address}")
            max_retries = 30
            ssh = None
            
            for i in range(max_retries):
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    if jump_host:
                        # Use Proxmox as SSH jump host
                        logger.info(f"Using SSH jump host: {jump_host}")
                        jump_user = current_app.config.get('SSH_JUMP_USER', 'root')
                        jump_password = current_app.config.get('SSH_JUMP_PASSWORD', '')
                        
                        # Connect to jump host (Proxmox)
                        jump_client = paramiko.SSHClient()
                        jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        jump_client.connect(
                            jump_host,
                            username=jump_user,
                            password=jump_password,
                            timeout=10
                        )
                        
                        # Create a channel to the target through the jump host
                        jump_transport = jump_client.get_transport()
                        dest_addr = (ip_address, 22)
                        local_addr = ('127.0.0.1', 0)
                        channel = jump_transport.open_channel('direct-tcpip', dest_addr, local_addr)
                        
                        # Connect to target VM through the channel
                        ssh.connect(
                            ip_address,
                            username=ssh_user,
                            key_filename=str(private_key_path),
                            sock=channel,
                            timeout=10,
                            look_for_keys=False,
                            allow_agent=False
                        )
                        logger.info(f"SSH connection established to {ip_address} via jump host {jump_host}")
                    else:
                        # Direct connection (same network)
                        ssh.connect(
                            ip_address, 
                            username=ssh_user, 
                            key_filename=str(private_key_path),
                            timeout=10,
                            look_for_keys=False,
                            allow_agent=False
                        )
                        logger.info(f"SSH connection established to {ip_address} (direct)")
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"SSH connection failed after {max_retries} attempts: {e}")
                    logger.warning(f"SSH connection attempt {i+1} failed: {e}")
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
        wait_for_lock = "while fuser /var/lib/dpkg/lock >/dev/null 2>&1 || fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo 'Waiting for apt lock...'; sleep 2; done"
        
        # Step 1: Update system and install base dependencies
        base_cmd = (
            f"export DEBIAN_FRONTEND=noninteractive && "
            f"{wait_for_lock} && "
            f"apt-get update -y && "
            f"{wait_for_lock} && "
            f"apt-get install -y apt-utils git curl wget build-essential"
        )
        commands.append(base_cmd)
        
        # Step 2: Language-specific installation
        if language == 'nodejs':
            node_cmd = (
                f"export DEBIAN_FRONTEND=noninteractive && "
                f"{wait_for_lock} && "
                f"curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && "
                f"{wait_for_lock} && "
                f"apt-get install -y nodejs && "
                f"npm install -g pm2 serve"
            )
            commands.append(node_cmd)
            
        elif language == 'python':
            py_cmd = (
                f"export DEBIAN_FRONTEND=noninteractive && "
                f"{wait_for_lock} && "
                f"apt-get install -y python3 python3-pip python3-venv"
            )
            commands.append(py_cmd)
            
        elif language == 'php':
            php_cmd = (
                f"export DEBIAN_FRONTEND=noninteractive && "
                f"{wait_for_lock} && "
                f"apt-get install -y php php-cli php-fpm php-mysql php-xml php-mbstring composer"
            )
            commands.append(php_cmd)
        
        # Step 3: Create app directory and clone repository
        commands.append('rm -rf /opt/app && mkdir -p /opt/app')
        commands.append(f'git clone --depth 1 {github_url} /opt/app')
        
        # Step 3.5: Fix Windows line endings (CRLF -> LF) for repos created on Windows
        commands.append(
            'apt-get install -y dos2unix && '
            'find /opt/app -type f \\( -name "*.js" -o -name "*.py" -o -name "*.sh" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.html" -o -name "*.css" -o -name "*.yml" -o -name "*.yaml" -o -name "*.env*" -o -name "Dockerfile*" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" \\) -exec dos2unix {} \\; 2>/dev/null || true'
        )
        
        # Step 4: Create .env file if env_vars provided
        if env_vars:
            env_lines = []
            for k, v in env_vars.items():
                env_lines.append(f'{k}={v}')
            env_content = '\\n'.join(env_lines)
            commands.append(f'echo -e "{env_content}" > /opt/app/.env')
        
        # Step 5: Install dependencies and start application based on framework
        if framework == 'react':
            # React: Install, build, serve with PM2
            # NODE_OPTIONS fixes OpenSSL 3.0 compatibility with older webpack
            # Handles both Vite (dist) and CRA (build) output directories
            install_and_start = (
                "cd /opt/app && "
                "export NODE_OPTIONS=--openssl-legacy-provider && "
                "npm install --legacy-peer-deps 2>&1 | tail -20 && "
                "(npm run build 2>&1 | tail -30 || true) && "
                "pm2 delete react-app 2>/dev/null || true && "
                "BUILD_DIR=$(if [ -d 'dist' ]; then echo 'dist'; elif [ -d 'build' ]; then echo 'build'; else echo '.'; fi) && "
                f"pm2 serve $BUILD_DIR {port} --name react-app --spa && "
                "pm2 save && "
                "pm2 startup systemd -u root --hp /root 2>/dev/null || true"
            )
            commands.append(install_and_start)
            
        elif framework == 'vuejs':
            # Vue.js: Install, build, serve with PM2
            # NODE_OPTIONS fixes OpenSSL 3.0 compatibility with older webpack
            install_and_start = (
                "cd /opt/app && "
                "export NODE_OPTIONS=--openssl-legacy-provider && "
                "npm install --legacy-peer-deps 2>&1 | tail -20 && "
                "npm run build 2>&1 | tail -20 && "
                "pm2 delete vue-app 2>/dev/null || true && "
                f"pm2 serve dist {port} --name vue-app --spa && "
                "pm2 save && "
                "pm2 startup systemd -u root --hp /root 2>/dev/null || true"
            )
            commands.append(install_and_start)
            
        elif framework == 'nextjs':
            # Next.js: Install, build, start with PM2
            # NODE_OPTIONS fixes OpenSSL 3.0 compatibility with older webpack
            install_and_start = (
                "cd /opt/app && "
                "export NODE_OPTIONS=--openssl-legacy-provider && "
                "npm install --legacy-peer-deps 2>&1 | tail -20 && "
                "npm run build 2>&1 | tail -20 && "
                "pm2 delete nextjs-app 2>/dev/null || true && "
                "pm2 start npm --name nextjs-app -- start && "
                "pm2 save && "
                "pm2 startup systemd -u root --hp /root 2>/dev/null || true"
            )
            commands.append(install_and_start)
            
        elif framework == 'express':
            # Express.js: Install and start with PM2
            install_and_start = (
                "cd /opt/app && "
                "npm install 2>&1 | tail -20 && "
                "pm2 delete express-app 2>/dev/null || true && "
                "pm2 start npm --name express-app -- start && "
                "pm2 save && "
                "pm2 startup systemd -u root --hp /root 2>/dev/null || true"
            )
            commands.append(install_and_start)
            
        elif framework == 'django':
            # Django: Create venv, install deps, run with gunicorn
            install_and_start = (
                "cd /opt/app && "
                "python3 -m venv venv && "
                "source venv/bin/activate && "
                "pip install --upgrade pip && "
                "pip install -r requirements.txt gunicorn 2>&1 | tail -20 && "
                "python manage.py migrate --noinput 2>&1 || true && "
                "python manage.py collectstatic --noinput 2>&1 || true && "
                f"nohup venv/bin/gunicorn --bind 0.0.0.0:{port} --workers 2 --daemon --access-logfile /var/log/app-access.log --error-logfile /var/log/app-error.log $(find . -name 'wsgi.py' | head -1 | sed 's|./||;s|/|.|g;s|.py||'):application"
            )
            commands.append(install_and_start)
            
        elif framework == 'flask':
            # Flask: Create venv, install deps, run with gunicorn
            install_and_start = (
                "cd /opt/app && "
                "python3 -m venv venv && "
                "source venv/bin/activate && "
                "pip install --upgrade pip && "
                "pip install -r requirements.txt gunicorn 2>&1 | tail -20 && "
                f"nohup venv/bin/gunicorn --bind 0.0.0.0:{port} --workers 2 --daemon --access-logfile /var/log/app-access.log --error-logfile /var/log/app-error.log app:app"
            )
            commands.append(install_and_start)
            
        elif framework == 'fastapi':
            # FastAPI: Create venv, install deps, run with uvicorn
            install_and_start = (
                "cd /opt/app && "
                "python3 -m venv venv && "
                "source venv/bin/activate && "
                "pip install --upgrade pip && "
                "pip install -r requirements.txt uvicorn 2>&1 | tail -20 && "
                f"nohup venv/bin/uvicorn main:app --host 0.0.0.0 --port {port} > /var/log/app.log 2>&1 &"
            )
            commands.append(install_and_start)
            
        elif framework == 'laravel':
            # Laravel: Install composer deps, setup
            install_and_start = (
                "cd /opt/app && "
                "composer install --no-dev --optimize-autoloader 2>&1 | tail -20 && "
                "cp .env.example .env 2>/dev/null || true && "
                "php artisan key:generate 2>&1 || true && "
                "php artisan migrate --force 2>&1 || true && "
                f"nohup php artisan serve --host=0.0.0.0 --port={port} > /var/log/app.log 2>&1 &"
            )
            commands.append(install_and_start)
            
        else:
            # Generic Node.js app: Install and start with PM2
            install_and_start = (
                "cd /opt/app && "
                "npm install 2>&1 | tail -20 && "
                "pm2 delete app 2>/dev/null || true && "
                "pm2 start npm --name app -- start && "
                "pm2 save"
            )
            commands.append(install_and_start)
        
        # Step 6: Verify app is running (optional status check)
        commands.append("sleep 3 && (pm2 list 2>/dev/null || ps aux | grep -E 'gunicorn|uvicorn|node|php' | grep -v grep | head -5)")
        
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
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            import requests
            
            # Suppress SSL warnings
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            
            proxmox_url = current_app.config['PROXMOX_URL']
            
            # Simple parsing logic
            if '://' in proxmox_url:
                host = proxmox_url.split('://')[1].split(':')[0]
            else:
                host = proxmox_url.split(':')[0]
                
            proxmox_host = host
            
            # Connect to Proxmox API
            proxmox = ProxmoxAPI(
                proxmox_host,
                user=current_app.config['PROXMOX_USER'],
                password=current_app.config['PROXMOX_PASSWORD'],
                verify_ssl=False,
                timeout=5
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
    
    def _generate_vm_id(self) -> int:
        """
        Generate a unique VM ID by checking both Proxmox and the database
        
        Returns:
            Unique VM ID (100-999 range for safety)
        """
        import random
        from backend.models.deployment import Deployment
        
        # Get VM IDs from the database
        db_vm_ids = set(Deployment.get_used_vm_ids())
        
        # Get VM IDs from Proxmox
        proxmox_vm_ids = set()
        try:
            proxmox_vm_ids = self._get_proxmox_vm_ids()
        except Exception as e:
            logger.warning(f"Could not fetch VM IDs from Proxmox: {e}")
        
        # Combine all used IDs
        used_ids = db_vm_ids.union(proxmox_vm_ids)
        
        # Generate unique ID
        max_attempts = 100
        for _ in range(max_attempts):
            vm_id = random.randint(100, 999)
            if vm_id not in used_ids:
                logger.info(f"Generated unique VM ID: {vm_id}")
                return vm_id
        
        # If we can't find a random ID, use sequential search
        for vm_id in range(100, 1000):
            if vm_id not in used_ids:
                logger.info(f"Generated sequential VM ID: {vm_id}")
                return vm_id
        
        raise Exception("No available VM IDs in range 100-999")
    
    def _get_proxmox_vm_ids(self) -> set:
        """
        Get all existing VM/LXC IDs from Proxmox
        
        Returns:
            Set of VM IDs currently in use on Proxmox
        """
        try:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            import requests
            
            # Suppress SSL warnings
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            
            proxmox_url = current_app.config['PROXMOX_URL']
            
            # Parse host from URL
            if '://' in proxmox_url:
                host = proxmox_url.split('://')[1].split(':')[0]
            else:
                host = proxmox_url.split(':')[0]
            
            # Connect to Proxmox API
            proxmox = ProxmoxAPI(
                host,
                user=current_app.config['PROXMOX_USER'],
                password=current_app.config['PROXMOX_PASSWORD'],
                verify_ssl=False,
                timeout=5
            )
            
            node = current_app.config['PROXMOX_NODE']
            vm_ids = set()
            
            # Get QEMU VMs
            try:
                qemu_vms = proxmox.nodes(node).qemu.get()
                for vm in qemu_vms:
                    if 'vmid' in vm:
                        vm_ids.add(int(vm['vmid']))
            except Exception as e:
                logger.warning(f"Could not fetch QEMU VMs: {e}")
            
            # Get LXC containers
            try:
                lxc_containers = proxmox.nodes(node).lxc.get()
                for ct in lxc_containers:
                    if 'vmid' in ct:
                        vm_ids.add(int(ct['vmid']))
            except Exception as e:
                logger.warning(f"Could not fetch LXC containers: {e}")
            
            logger.info(f"Found {len(vm_ids)} existing VM/LXC IDs in Proxmox")
            return vm_ids
            
        except Exception as e:
            logger.error(f"Error fetching VM IDs from Proxmox: {e}")
            return set()
