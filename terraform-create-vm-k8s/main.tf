locals {
  vm_groups = [
    jsondecode(file("${path.root}/list_vm/vm_templates.json"))
  ]
  vm_configs = merge(local.vm_groups...)
  
  common_vm_settings = {
    resource_pool_id = data.vsphere_compute_cluster.cluster.resource_pool_id
    datastore_id     = data.vsphere_datastore.datastores["ds2"].id
    network_id       = data.vsphere_network.network.id
    dns_servers      = ["10.0.6.3"]
    domain          = "idevops.io.vn"
    ipv4_gateway    = "10.0.6.2"
    ipv4_netmask    = 24
  }
}

module "vcenter_vms" {
  source = "./modules/vcenter_vm"
  for_each = local.vm_configs
  
  # Merge all settings
  vm_name          = each.key
  template_uuid    = data.vsphere_virtual_machine.template[each.key].id
  guest_id         = each.value.guest_id
  num_cpus         = each.value.num_cpus
  memory           = each.value.memory
  vm_hostname      = each.value.host_name
  ipv4_address     = each.value.ipv4_address

  # Use common settings
  resource_pool_id = local.common_vm_settings.resource_pool_id
  datastore_id     = local.common_vm_settings.datastore_id
  network_id       = local.common_vm_settings.network_id
  domain           = local.common_vm_settings.domain
  ipv4_netmask     = local.common_vm_settings.ipv4_netmask
  ipv4_gateway     = local.common_vm_settings.ipv4_gateway
  dns_servers      = local.common_vm_settings.dns_servers

  # Credentials
  GOVC_URL         = var.GOVC_URL
  GOVC_USERNAME    = var.GOVC_USERNAME
  GOVC_PASSWORD    = var.GOVC_PASSWORD
}
