locals {
  vm_groups = [
    jsondecode(file("${path.root}/list_vm/vm_templates.json"))
  ]
  vm_configs = merge(local.vm_groups...)
}

module "vcenter_vms" {
  source               = "./modules/vcenter_vm"
  for_each             = local.vm_configs
  vm_name              = each.key
  resource_pool_id     = data.vsphere_compute_cluster.cluster.resource_pool_id
  datastore_id         = data.vsphere_datastore.ds2.id
  network_id           = data.vsphere_network.network.id
  template_uuid        = data.vsphere_virtual_machine.template[each.key].id
  guest_id             = each.value.guest_id
  num_cpus             = each.value.num_cpus
  memory               = each.value.memory
  vm_hostname          = each.value.host_name
  domain               = each.value.domain
  ipv4_address         = each.value.ipv4_address
  ipv4_netmask         = each.value.ipv4_netmask
  ipv4_gateway         = each.value.ipv4_gateway
  GOVC_URL            = var.GOVC_URL
  GOVC_USERNAME       = var.GOVC_USERNAME
  GOVC_PASSWORD       = var.GOVC_PASSWORD
}

