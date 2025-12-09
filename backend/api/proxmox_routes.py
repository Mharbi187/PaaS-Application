from flask import Blueprint, jsonify, current_app
import logging
from proxmoxer import ProxmoxAPI

api_proxmox_bp = Blueprint('api_proxmox', __name__)
logger = logging.getLogger(__name__)

def get_proxmox_connection():
    """Establish connection to Proxmox API"""
    try:
        import re
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
            
        logger.info(f"Connecting to Proxmox at {host} as {current_app.config['PROXMOX_USER']}")
        
        return ProxmoxAPI(
            host,
            user=current_app.config['PROXMOX_USER'],
            password=current_app.config['PROXMOX_PASSWORD'],
            verify_ssl=False,
            timeout=5
        )
    except Exception as e:
        logger.error(f"Failed to connect to Proxmox: {e}")
        raise

@api_proxmox_bp.route('/proxmox/nodes', methods=['GET'])
def list_proxmox_nodes():
    """
    List all nodes in the Proxmox cluster
    """
    try:
        proxmox = get_proxmox_connection()
        
        # Test connection by listing nodes
        # This is the most basic call that should work if auth is correct
        nodes = proxmox.nodes.get()
        
        # Log successful node retrieval
        logger.info(f"Successfully retrieved nodes: {[n.get('node') for n in nodes]}")
        
        return jsonify({
            'success': True,
            'nodes': nodes
        })
    except Exception as e:
        logger.error(f"Error listing nodes: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Failed to list nodes: {str(e)}"
        }), 500

@api_proxmox_bp.route('/proxmox/nodes/<node>/vms', methods=['GET'])
def list_node_vms(node):
    """
    List all VMs and LXC containers on a specific node
    """
    try:
        proxmox = get_proxmox_connection()
        
        # Get QEMU VMs
        vms = proxmox.nodes(node).qemu.get()
        
        # Get LXC Containers
        lxcs = proxmox.nodes(node).lxc.get()
        
        # Combine and format
        all_resources = []
        
        for vm in vms:
            all_resources.append({
                'id': vm.get('vmid'),
                'name': vm.get('name'),
                'type': 'qemu',
                'status': vm.get('status'),
                'memory': vm.get('maxmem'),
                'cores': vm.get('cpus'),
                'uptime': vm.get('uptime')
            })
            
        for lxc in lxcs:
            all_resources.append({
                'id': lxc.get('vmid'),
                'name': lxc.get('name'),
                'type': 'lxc',
                'status': lxc.get('status'),
                'memory': lxc.get('maxmem'),
                'cores': lxc.get('cpus'),
                'uptime': lxc.get('uptime')
            })
            
        return jsonify({
            'success': True,
            'resources': all_resources
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
