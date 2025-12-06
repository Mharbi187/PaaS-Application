# Terraform configuration for Proxmox PaaS Platform

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = "2.9.10"  # Version compatible avec Proxmox 6.x (pas de VM.Monitor requis)
    }
  }
}

# Configure the Proxmox Provider
provider "proxmox" {
  pm_api_url      = var.proxmox_url
  pm_user         = var.proxmox_user
  pm_password     = var.proxmox_password
  pm_tls_insecure = true
  pm_log_enable   = true
  pm_log_file     = "terraform-plugin-proxmox.log"
  pm_debug        = true
  pm_log_levels = {
    _default    = "debug"
    _capturelog = ""
  }
}

# Conditional VM resource
resource "proxmox_vm_qemu" "deployment_vm" {
  count = var.deployment_type == "vm" ? 1 : 0
  
  name        = var.deployment_name
  target_node = var.proxmox_node
  vmid        = var.vm_id
  
  # Clone from cloud-init template or use ISO
  clone = var.vm_template != "" ? var.vm_template : null
  
  # VM Settings
  cores   = var.cores
  sockets = 1
  memory  = var.memory
  
  # Network configuration
  network {
    model  = "virtio"
    bridge = var.network_bridge
  }
  
  # Disk configuration
  disk {
    type    = "scsi"
    storage = var.proxmox_storage
    size    = "${var.disk_size}G"
  }
  
  # Cloud-init settings
  os_type   = "cloud-init"
  ipconfig0 = "ip=dhcp"
  
  # SSH keys (join list into newline-separated string)
  sshkeys = length(var.ssh_public_keys) > 0 ? join("\n", var.ssh_public_keys) : (var.ssh_public_key != "" ? var.ssh_public_key : null)
  
  # Start VM after creation
  onboot = true
  
  # Lifecycle
  lifecycle {
    ignore_changes = [
      network,
      disk,
    ]
  }
  
  # Tags
  tags = "paas,${var.framework},${var.deployment_type}"
}

# Conditional LXC resource
resource "proxmox_lxc" "deployment_lxc" {
  count = var.deployment_type == "lxc" ? 1 : 0
  
  hostname    = var.deployment_name
  target_node = var.proxmox_node
  vmid        = var.vm_id
  
  # Container template (os_template already contains full volid like "local:vztmpl/ubuntu...")
  ostemplate = var.os_template
  
  # Container resources
  cores  = var.cores
  memory = var.memory
  swap   = var.memory / 2
  
  # Root filesystem
  rootfs {
    storage = var.proxmox_storage
    size    = "${var.disk_size}G"
  }
  
  # Network configuration
  network {
    name   = "eth0"
    bridge = var.network_bridge
    ip     = "dhcp"
  }
  
  # Container settings
  unprivileged = false
  onboot       = true
  start        = true
  
  # SSH keys (preferred method)
  ssh_public_keys = length(var.ssh_public_keys) > 0 ? join("\n", var.ssh_public_keys) : (var.ssh_public_key != "" ? var.ssh_public_key : null)
  
  # Tags
  tags = "paas,${var.framework},${var.deployment_type}"
}
