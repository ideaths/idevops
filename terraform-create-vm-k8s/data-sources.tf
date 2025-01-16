locals {
  vsphere_config = {
    datacenter = "Home"
    cluster    = "Home"
    datastores = {
      ds1 = "datastore1"
      ds2 = "datastore2"
    }
  }
}

data "vsphere_datacenter" "dc" {
  name = local.vsphere_config.datacenter
}

data "vsphere_compute_cluster" "cluster" {
  name          = local.vsphere_config.cluster
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_datastore" "datastores" {
  for_each      = local.vsphere_config.datastores
  name          = each.value
  datacenter_id = data.vsphere_datacenter.dc.id
}

# Add network data source
data "vsphere_network" "network" {
  name          = "VM Network"
  datacenter_id = data.vsphere_datacenter.dc.id
}

# Add template data source
data "vsphere_virtual_machine" "template" {
  for_each      = local.vm_configs
  name          = each.value.vm_type
  datacenter_id = data.vsphere_datacenter.dc.id
}
