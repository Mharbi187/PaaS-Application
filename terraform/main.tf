# Terraform configuration for Proxmox PaaS Platform

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.46.1"
    }
  }
}

# Configure the Proxmox Provider
provider "proxmox" {
  endpoint = var.proxmox_url
  username = var.proxmox_user
  password = var.proxmox_password
  insecure = true
  
  # Optional: API Token authentication is preferred if available
  # api_token = "..."
}

# Conditional VM resource
# Conditional VM resource
resource "proxmox_virtual_environment_vm" "deployment_vm" {
  count = var.deployment_type == "vm" ? 1 : 0
  
  name      = var.deployment_name
  node_name = var.proxmox_node
  vm_id     = var.vm_id
  
  # Clone settings (if using template)
  # For bpg provider, cloning is handled differently. 
  # We will use a simple ISO boot or Template clone if specified.
  
  cpu {
    cores = var.cores
    sockets = 1
  }

  memory {
    dedicated = var.memory
  }
  
  network_device {
    bridge = var.network_bridge
    model  = "virtio"
  }
  
  disk {
    datastore_id = var.proxmox_storage
    file_format  = "raw"
    interface    = "scsi0"
    size         = var.disk_size
  }
  
  operating_system {
    type = "l26" # Linux 2.6+
  }

  initialization {
    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }
    
    user_account {
      keys = length(var.ssh_public_keys) > 0 ? var.ssh_public_keys : (var.ssh_public_key != "" ? [var.ssh_public_key] : [])
    }
  }
  
  started = true
}

# Conditional LXC resource
# Conditional LXC resource
resource "proxmox_virtual_environment_container" "deployment_lxc" {
  count = var.deployment_type == "lxc" ? 1 : 0
  
  description = "Managed by PaaS Platform"
  node_name   = var.proxmox_node
  vm_id       = var.vm_id
  
  initialization {
    hostname = var.deployment_name
    
    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }
    
    user_account {
      keys = length(var.ssh_public_keys) > 0 ? var.ssh_public_keys : (var.ssh_public_key != "" ? [var.ssh_public_key] : [])
    }
  }

  network_interface {
    name   = "eth0"
    bridge = var.network_bridge
  }
  
  operating_system {
    template_file_id = var.os_template
    type             = "ubuntu" # or debian, etc.
  }

  # Container resources
  cpu {
    cores = var.cores
  }
  
  memory {
    dedicated = var.memory
    swap      = 512
  }
  
  disk {
    datastore_id = var.proxmox_storage
    size         = var.disk_size
  }
  
  unprivileged = true
  started      = true
  
  tags = ["paas", var.framework, var.deployment_type]
}
