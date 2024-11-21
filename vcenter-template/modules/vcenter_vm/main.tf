resource "vsphere_virtual_machine" "vm" {
  name             = var.vm_name
  resource_pool_id = var.resource_pool_id
  datastore_id     = var.datastore_id
  guest_id         = var.guest_id
  num_cpus         = local.num_cpus
  memory           = local.memory

  # Khối cấu hình mạng
  network_interface {
    network_id   = local.network_interface[0].network_id
    adapter_type = local.network_interface[0].adapter_type
  }

  # Khối cấu hình đĩa
  disk {
    label            = local.disk[0].label
    size             = local.disk[0].size
    eagerly_scrub    = local.disk[0].eagerly_scrub
    thin_provisioned = local.disk[0].thin_provisioned
  }

  # Khối cấu hình CD-ROM
  cdrom {
    datastore_id = local.cdrom.datastore_id
    path         = local.cdrom.path
  }

  boot_delay                = var.boot_delay
  wait_for_guest_net_timeout = var.wait_for_guest_net_timeout
}
