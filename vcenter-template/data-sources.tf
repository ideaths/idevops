data "vsphere_datacenter" "dc" {
  name = "Home"
}

data "vsphere_compute_cluster" "cluster" {
  name          = "Home"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_datastore" "ds1" {
  name          = "datastore1"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_datastore" "ds2" {
  name          = "datastore2"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = "VM Network"
  datacenter_id = data.vsphere_datacenter.dc.id
}
