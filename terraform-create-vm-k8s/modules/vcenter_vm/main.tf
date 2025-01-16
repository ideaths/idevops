locals {
  vm_config = {
    network = {
      network_id   = var.network_id
      adapter_type = var.adapter_type
    }
    disk = {
      label            = "disk0"
      size             = var.disk_size
      eagerly_scrub    = var.eagerly_scrub
      thin_provisioned = var.thin_provisioned
    }
    customize = {
      linux = {
        host_name = var.vm_hostname
        domain    = var.domain
      }
      network = {
        ipv4_address = var.ipv4_address
        ipv4_netmask = var.ipv4_netmask
      }
    }
  }
}

resource "vsphere_virtual_machine" "vm" {
  force_power_off  = true
  name             = var.vm_name
  resource_pool_id = var.resource_pool_id
  datastore_id     = var.datastore_id
  num_cpus         = var.num_cpus
  memory           = var.memory
  guest_id         = var.guest_id
  wait_for_guest_net_timeout = 0

  network_interface {
    network_id   = local.vm_config.network.network_id
    adapter_type = local.vm_config.network.adapter_type
  }
  
  disk {
    label            = local.vm_config.disk.label
    size             = local.vm_config.disk.size
    eagerly_scrub    = local.vm_config.disk.eagerly_scrub
    thin_provisioned = local.vm_config.disk.thin_provisioned
  }

  clone {
    template_uuid = var.template_uuid
    customize {
      linux_options {
        host_name = local.vm_config.customize.linux.host_name
        domain    = local.vm_config.customize.linux.domain
      }
      network_interface {
        ipv4_address = local.vm_config.customize.network.ipv4_address
        ipv4_netmask = local.vm_config.customize.network.ipv4_netmask
      }
      ipv4_gateway    = var.ipv4_gateway
      dns_server_list = var.dns_servers
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}