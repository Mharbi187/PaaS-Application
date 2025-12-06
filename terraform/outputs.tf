# Terraform Outputs

output "vm_id" {
  description = "VM/LXC ID"
  value       = var.vm_id
}

output "deployment_name" {
  description = "Deployment name"
  value       = var.deployment_name
}

output "deployment_type" {
  description = "Deployment type"
  value       = var.deployment_type
}

output "framework" {
  description = "Application framework"
  value       = var.framework
}

output "ip_address" {
  description = "IP address of the deployment"
  value = var.deployment_type == "vm" ? (
    length(proxmox_vm_qemu.deployment_vm) > 0 ? 
    try(proxmox_vm_qemu.deployment_vm[0].default_ipv4_address, "pending") : 
    "pending"
  ) : (
    length(proxmox_lxc.deployment_lxc) > 0 ?
    "Check Proxmox Console" : # LXC IP is hard to get via Terraform with DHCP
    "pending"
  )
}

output "access_url" {
  description = "Access URL for the deployed application"
  value = var.deployment_type == "vm" ? (
    length(proxmox_vm_qemu.deployment_vm) > 0 ?
    "http://${try(proxmox_vm_qemu.deployment_vm[0].default_ipv4_address, "pending")}:${var.framework_port}" :
    "pending"
  ) : (
    length(proxmox_lxc.deployment_lxc) > 0 ?
    "http://<LXC_IP>:${var.framework_port}" :
    "pending"
  )
}

output "resources" {
  description = "Allocated resources"
  value = {
    cores  = var.cores
    memory = var.memory
    disk   = var.disk_size
  }
}

output "status" {
  description = "Deployment status"
  value       = "provisioned"
}
