"""
API Routes for PaaS Platform
Handles deployment requests and infrastructure management
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from backend.api.terraform_manager import TerraformManager
from backend.utils.validators import validate_deployment_request
from backend.models.deployment import Deployment, DeploymentStatus
from backend.extensions import db
from datetime import datetime

# Create blueprint
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


def get_terraform_manager():
    """Get the Terraform manager"""
    return TerraformManager()


@api_bp.route('/frameworks', methods=['GET'])
def get_frameworks():
    """
    Get list of supported frameworks
    
    Returns:
        JSON response with supported frameworks
    """
    try:
        frameworks = current_app.config['SUPPORTED_FRAMEWORKS']
        return jsonify({
            'success': True,
            'frameworks': frameworks
        })
    except Exception as e:
        logger.error(f"Error fetching frameworks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/deploy', methods=['POST'])
def deploy_application():
    """
    Deploy a new application
    
    Request body:
        - deployment_type: 'vm' or 'lxc'
        - framework: Framework identifier
        - github_url: GitHub repository URL
        - name: Deployment name
        - resources: CPU, memory, disk configuration
    
    Returns:
        JSON response with deployment status and details
    """
    deployment = None
    try:
        # Get request data
        data = request.get_json()
        logger.info(f"Received deployment request: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate request
        is_valid, errors = validate_deployment_request(data)
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        # Extract deployment parameters
        deployment_type = data.get('deployment_type')
        framework = data.get('framework')
        github_url = data.get('github_url')
        name = data.get('name')
        resources = data.get('resources', {})
        env_vars = data.get('env_vars', {})  # Optional environment variables
        
        # Create deployment record
        deployment = Deployment(
            name=name,
            deployment_type=deployment_type,
            framework=framework,
            github_url=github_url,
            resources=resources,
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Save initial deployment record to database
        db.session.add(deployment)
        db.session.commit()
        
        logger.info(f"Starting automated deployment: {name} (ID: {deployment.id})")
        logger.info(f"Framework: {framework}, Type: {deployment_type}, Repo: {github_url}")
        
        # Initialize Terraform manager
        terraform_manager = get_terraform_manager()
        
        # Generate Terraform configuration
        logger.info(f"Generating Terraform configuration...")
        tf_config = terraform_manager.generate_config(
            deployment_type=deployment_type,
            framework=framework,
            name=name,
            resources=resources
        )
        
        # Apply Terraform configuration to provision infrastructure
        logger.info(f"Provisioning {deployment_type.upper()} infrastructure on Proxmox...")
        deployment.status = DeploymentStatus.PROVISIONING
        db.session.commit()
        
        result = terraform_manager.apply(name, tf_config)
        
        if result['success']:
            deployment.status = DeploymentStatus.DEPLOYING
            deployment.ip_address = result.get('ip_address')
            deployment.vm_id = result.get('vm_id')
            db.session.commit()
            
            logger.info(f"Infrastructure provisioned: {deployment_type.upper()} ID {deployment.vm_id}, IP {deployment.ip_address}")
            logger.info(f"Deploying application via SSH...")
            
            # Deploy application directly via SSH
            deploy_result = terraform_manager.deploy_application(
                ip_address=deployment.ip_address,
                framework=framework,
                github_url=github_url,
                env_vars=env_vars
            )
            
            if deploy_result['success']:
                deployment.status = DeploymentStatus.RUNNING
                deployment.deployed_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Application deployed successfully on {deployment.ip_address}")
                
                return jsonify({
                    'success': True,
                    'message': 'Application deployed successfully',
                    'deployment': {
                        'id': deployment.id,
                        'name': deployment.name,
                        'ip_address': deployment.ip_address,
                        'vm_id': deployment.vm_id,
                        'status': deployment.status.value,
                        'framework': framework,
                        'access_url': deploy_result.get('access_url')
                    }
                })
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = deploy_result.get('error')
                db.session.commit()
                raise Exception(f"Application deployment failed: {deploy_result.get('error')}")
        
        else:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = result.get('error')
            db.session.commit()
            raise Exception(f"Infrastructure provisioning failed: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"Deployment error: {e}", exc_info=True)
        # Update deployment status if it exists
        if deployment:
            try:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = str(e)
                db.session.commit()
            except:
                db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'details': 'Check server logs for more information'
        }), 500


@api_bp.route('/deployments', methods=['GET'])
def list_deployments():
    """
    List all deployments
    
    Returns:
        JSON response with list of deployments
    """
    try:
        deployments = Deployment.get_all()
        return jsonify({
            'success': True,
            'deployments': [d.to_dict() for d in deployments]
        })
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/deployments/<deployment_id>', methods=['GET'])
def get_deployment(deployment_id):
    """
    Get deployment details
    
    Args:
        deployment_id: Deployment identifier
    
    Returns:
        JSON response with deployment details
    """
    try:
        deployment = Deployment.get_by_id(deployment_id)
        if not deployment:
            return jsonify({
                'success': False,
                'error': 'Deployment not found'
            }), 404
        
        return jsonify({
            'success': True,
            'deployment': deployment.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching deployment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/deployments/<deployment_id>', methods=['DELETE'])
def delete_deployment(deployment_id):
    """
    Delete a deployment
    
    Args:
        deployment_id: Deployment identifier
    
    Returns:
        JSON response with deletion status
    """
    try:
        deployment = Deployment.get_by_id(deployment_id)
        if not deployment:
            return jsonify({
                'success': False,
                'error': 'Deployment not found'
            }), 404
        
        # Initialize Terraform manager
        terraform_manager = get_terraform_manager()
        
        # Destroy Terraform resources
        result = terraform_manager.destroy(deployment.name)
        
        if result['success']:
            deployment.status = DeploymentStatus.DELETED
            deployment.deleted_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Deployment deleted successfully'
            })
        else:
            raise Exception(f"Failed to destroy infrastructure: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"Error deleting deployment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/deployments/<deployment_id>/logs', methods=['GET'])
def get_deployment_logs(deployment_id):
    """
    Get deployment logs
    
    Args:
        deployment_id: Deployment identifier
    
    Returns:
        JSON response with deployment logs
    """
    try:
        deployment = Deployment.get_by_id(deployment_id)
        if not deployment:
            return jsonify({
                'success': False,
                'error': 'Deployment not found'
            }), 404
        
        # Initialize Terraform manager
        terraform_manager = get_terraform_manager()
        
        logs = terraform_manager.get_logs(deployment.name)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get platform statistics
    
    Returns:
        JSON response with platform statistics
    """
    try:
        total_deployments = Deployment.count_all()
        running_deployments = Deployment.count_by_status(DeploymentStatus.RUNNING)
        failed_deployments = Deployment.count_by_status(DeploymentStatus.FAILED)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_deployments': total_deployments,
                'running_deployments': running_deployments,
                'failed_deployments': failed_deployments,
                'success_rate': (running_deployments / total_deployments * 100) if total_deployments > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/proxmox/resources', methods=['GET'])
def get_proxmox_resources():
    """
    Get all VMs and LXC containers from Proxmox
    
    Returns:
        JSON response with Proxmox resources
    """
    try:
        from proxmoxer import ProxmoxAPI
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
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
            timeout=10
        )
        
        node = current_app.config['PROXMOX_NODE']
        resources = []
        
        # Get QEMU VMs
        try:
            qemu_vms = proxmox.nodes(node).qemu.get()
            for vm in qemu_vms:
                resources.append({
                    'vmid': vm.get('vmid'),
                    'name': vm.get('name', f"VM-{vm.get('vmid')}"),
                    'type': 'vm',
                    'status': vm.get('status'),
                    'cpu': vm.get('cpus', 0),
                    'memory': vm.get('maxmem', 0) // (1024 * 1024),  # Convert to MB
                    'disk': vm.get('maxdisk', 0) // (1024 * 1024 * 1024),  # Convert to GB
                    'uptime': vm.get('uptime', 0)
                })
        except Exception as e:
            logger.warning(f"Could not fetch QEMU VMs: {e}")
        
        # Get LXC containers
        try:
            lxc_containers = proxmox.nodes(node).lxc.get()
            for ct in lxc_containers:
                resources.append({
                    'vmid': ct.get('vmid'),
                    'name': ct.get('name', f"CT-{ct.get('vmid')}"),
                    'type': 'lxc',
                    'status': ct.get('status'),
                    'cpu': ct.get('cpus', 0),
                    'memory': ct.get('maxmem', 0) // (1024 * 1024),  # Convert to MB
                    'disk': ct.get('maxdisk', 0) // (1024 * 1024 * 1024),  # Convert to GB
                    'uptime': ct.get('uptime', 0)
                })
        except Exception as e:
            logger.warning(f"Could not fetch LXC containers: {e}")
        
        return jsonify({
            'success': True,
            'resources': resources,
            'count': len(resources)
        })
        
    except Exception as e:
        logger.error(f"Error fetching Proxmox resources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/proxmox/sync', methods=['POST'])
def sync_proxmox_resources():
    """
    Sync existing Proxmox VMs/LXCs into the dashboard database
    
    This imports existing Proxmox resources so they appear in the dashboard.
    Only imports resources that are not already tracked.
    
    Returns:
        JSON response with sync results
    """
    try:
        from proxmoxer import ProxmoxAPI
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
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
            timeout=10
        )
        
        node = current_app.config['PROXMOX_NODE']
        
        # Get already tracked VM IDs
        tracked_vm_ids = set(Deployment.get_used_vm_ids())
        
        imported = []
        skipped = []
        
        # Sync QEMU VMs
        try:
            qemu_vms = proxmox.nodes(node).qemu.get()
            for vm in qemu_vms:
                vmid = vm.get('vmid')
                if vmid in tracked_vm_ids:
                    skipped.append({'vmid': vmid, 'name': vm.get('name'), 'reason': 'already tracked'})
                    continue
                
                # Get IP address if possible
                ip_address = None
                try:
                    agent_info = proxmox.nodes(node).qemu(vmid).agent.get('network-get-interfaces')
                    if agent_info and agent_info.get('result'):
                        for iface in agent_info['result']:
                            if iface.get('name') in ['eth0', 'ens18']:
                                for ip_addr in iface.get('ip-addresses', []):
                                    if ip_addr.get('ip-address-type') == 'ipv4':
                                        ip = ip_addr.get('ip-address')
                                        if ip and not ip.startswith('127.'):
                                            ip_address = ip
                                            break
                except:
                    pass
                
                # Create deployment record
                deployment = Deployment(
                    name=vm.get('name', f"vm-{vmid}"),
                    deployment_type='vm',
                    framework='unknown',
                    github_url='imported-from-proxmox',
                    resources={
                        'cores': vm.get('cpus', 1),
                        'memory': vm.get('maxmem', 0) // (1024 * 1024),
                        'disk': vm.get('maxdisk', 0) // (1024 * 1024 * 1024)
                    },
                    status=DeploymentStatus.RUNNING if vm.get('status') == 'running' else DeploymentStatus.STOPPED,
                    created_at=datetime.utcnow()
                )
                deployment.vm_id = vmid
                deployment.ip_address = ip_address
                db.session.add(deployment)
                
                imported.append({
                    'vmid': vmid,
                    'name': vm.get('name'),
                    'type': 'vm',
                    'ip_address': ip_address
                })
                
        except Exception as e:
            logger.warning(f"Could not sync QEMU VMs: {e}")
        
        # Sync LXC containers
        try:
            lxc_containers = proxmox.nodes(node).lxc.get()
            for ct in lxc_containers:
                vmid = ct.get('vmid')
                if vmid in tracked_vm_ids:
                    skipped.append({'vmid': vmid, 'name': ct.get('name'), 'reason': 'already tracked'})
                    continue
                
                # Get IP address if possible
                ip_address = None
                try:
                    interfaces = proxmox.nodes(node).lxc(vmid).interfaces.get()
                    if interfaces:
                        for interface in interfaces:
                            if interface.get('name') == 'eth0' and 'inet' in interface:
                                ip = interface['inet'].split('/')[0]
                                if ip and ip != '0.0.0.0':
                                    ip_address = ip
                                    break
                except:
                    pass
                
                # Create deployment record
                deployment = Deployment(
                    name=ct.get('name', f"ct-{vmid}"),
                    deployment_type='lxc',
                    framework='unknown',
                    github_url='imported-from-proxmox',
                    resources={
                        'cores': ct.get('cpus', 1),
                        'memory': ct.get('maxmem', 0) // (1024 * 1024),
                        'disk': ct.get('maxdisk', 0) // (1024 * 1024 * 1024)
                    },
                    status=DeploymentStatus.RUNNING if ct.get('status') == 'running' else DeploymentStatus.STOPPED,
                    created_at=datetime.utcnow()
                )
                deployment.vm_id = vmid
                deployment.ip_address = ip_address
                db.session.add(deployment)
                
                imported.append({
                    'vmid': vmid,
                    'name': ct.get('name'),
                    'type': 'lxc',
                    'ip_address': ip_address
                })
                
        except Exception as e:
            logger.warning(f"Could not sync LXC containers: {e}")
        
        # Commit all imports
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Synced {len(imported)} resources from Proxmox",
            'imported': imported,
            'skipped': skipped,
            'imported_count': len(imported),
            'skipped_count': len(skipped)
        })
        
    except Exception as e:
        logger.error(f"Error syncing Proxmox resources: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
