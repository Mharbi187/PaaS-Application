# Terraform Variables for Proxmox PaaS Platform

# Deployment Configuration
variable "deployment_name" {
  description = "Name of the deployment"
  type        = string
}

variable "deployment_type" {
  description = "Type of deployment: vm or lxc"
  type        = string
  
  validation {
    condition     = contains(["vm", "lxc"], var.deployment_type)
    error_message = "Deployment type must be either 'vm' or 'lxc'."
  }
}

variable "vm_id" {
  description = "Unique VM/LXC ID"
  type        = number
}

variable "framework" {
  description = "Application framework"
  type        = string
}

variable "framework_language" {
  description = "Framework programming language"
  type        = string
}

variable "framework_port" {
  description = "Framework default port"
  type        = number
}

variable "github_url" {
  description = "GitHub repository URL"
  type        = string
  default     = ""
}

# Proxmox Configuration
variable "proxmox_url" {
  description = "Proxmox API URL"
  type        = string
}

variable "proxmox_user" {
  description = "Proxmox user"
  type        = string
}

variable "proxmox_password" {
  description = "Proxmox password"
  type        = string
  sensitive   = true
}

variable "proxmox_node" {
  description = "Proxmox node name"
  type        = string
}

variable "proxmox_storage" {
  description = "Proxmox storage name"
  type        = string
}

variable "template_storage" {
  description = "Proxmox storage for templates"
  type        = string
  default     = "local"
}

# Resource Configuration
variable "cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "memory" {
  description = "Memory in MB"
  type        = number
  default     = 2048
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

# Network Configuration
variable "network_bridge" {
  description = "Network bridge"
  type        = string
  default     = "vmbr0"
}

variable "gateway" {
  description = "Network gateway"
  type        = string
}

variable "dns_servers" {
  description = "DNS servers (comma-separated)"
  type        = string
  default     = "8.8.8.8,8.8.4.4"
}

# OS Templates
variable "os_template" {
  description = "LXC OS template"
  type        = string
  default     = "ubuntu-22.04-standard"
}

variable "iso_image" {
  description = "VM ISO image"
  type        = string
  default     = "ubuntu-22.04-server-amd64.iso"
}

variable "vm_template" {
  description = "VM template to clone from (optional)"
  type        = string
  default     = ""
}

# SSH Configuration
variable "ssh_public_key" {
  description = "SSH public key for access"
  type        = string
  default     = ""
}

variable "ssh_user" {
  description = "SSH username"
  type        = string
  default     = "root"
}

variable "ssh_password" {
  description = "SSH password (temporary, use SSH keys in production)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssh_public_keys" {
  description = "List of SSH public keys to add to the container"
  type        = list(string)
  default     = []
}
