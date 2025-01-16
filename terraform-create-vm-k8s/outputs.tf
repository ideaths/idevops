output "vm_ids" {
  description = "Map of VM names to their IDs"
  value       = { for k, v in module.vcenter_vms : k => v.vm_id }
}

output "vm_names" {
  description = "Map of VM names to their configured names"
  value       = { for k, v in module.vcenter_vms : k => v.vm_name }
}

output "vm_summary" {
  description = "Summary of all created VMs with their IPs"
  value = {
    for k, v in local.vm_configs : k => {
      hostname     = v.host_name
      ip_address   = v.ipv4_address
      cpu_cores    = v.num_cpus
      memory_mb    = v.memory
      vm_type      = v.vm_type
    }
  }
}
