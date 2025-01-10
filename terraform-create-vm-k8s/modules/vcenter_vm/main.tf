resource "vsphere_virtual_machine" "vm" {
  name             = var.vm_name
  resource_pool_id = var.resource_pool_id
  datastore_id     = var.datastore_id
  num_cpus         = var.num_cpus
  memory           = var.memory
  guest_id         = var.guest_id
  wait_for_guest_net_timeout = 0

  network_interface {
    network_id   = var.network_id
    adapter_type = var.adapter_type
  }
  
  disk {
    label            = "disk0"
    size             = var.disk_size
    eagerly_scrub    = var.eagerly_scrub
    thin_provisioned = var.thin_provisioned
  }

  clone {
    template_uuid = var.template_uuid
    customize {
      linux_options {
        host_name = var.vm_hostname
        domain    = var.domain
      }
      network_interface {
        ipv4_address = var.ipv4_address
        ipv4_netmask = var.ipv4_netmask
      }
      ipv4_gateway = "10.6.6.2"
      dns_server_list = ["10.6.6.129"]
    }
  }

  cdrom {
    client_device = true
  }

  provisioner "local-exec" {
    command = "sleep 60 && govc vm.power -reset ${self.name}"
    environment = {
      GOVC_URL      = var.GOVC_URL
      GOVC_USERNAME = var.GOVC_USERNAME
      GOVC_PASSWORD = var.GOVC_PASSWORD
      GOVC_INSECURE = "1"
    }
  }
  provisioner "local-exec" {
    command = "sleep 120 && govc snapshot.create -vm ${self.name} 'InitialSnapshot'"
    environment = {
      GOVC_URL      = var.GOVC_URL
      GOVC_USERNAME = var.GOVC_USERNAME
      GOVC_PASSWORD = var.GOVC_PASSWORD
      GOVC_INSECURE = "1"
    }
  }
}