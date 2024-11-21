output "vm_ids" {
  value = { for k, v in module.vcenter_vms : k => v.vm_id }
}

output "vm_names" {
  value = { for k, v in module.vcenter_vms : k => v.vm_name }
}
