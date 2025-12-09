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
    length(proxmox_virtual_environment_vm.deployment_vm) > 0 ? 
    try(proxmox_virtual_environment_vm.deployment_vm[0].ipv4_addresses[1][0], "pending") : 
    "pending"
  ) : (
    # LXC IPs are not directly exported in the same way. 
    # Since we use DHCP, we mark it as pending lookup.
    "Pending (Check Dashboard)"
  )
}

output "access_url" {
  description = "Access URL for the deployed application"
  value = var.deployment_type == "vm" ? (
    length(proxmox_virtual_environment_vm.deployment_vm) > 0 ?
    "http://${try(proxmox_virtual_environment_vm.deployment_vm[0].ipv4_addresses[1][0], "pending")}:${var.framework_port}" :
    "pending"
  ) : (
    # Fallback for LXC
    "http://<IP_PENDING>:${var.framework_port}"
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
