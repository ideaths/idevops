resource "null_resource" "vm_operations" {
  triggers = {
    vm_id = vsphere_virtual_machine.vm.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      max_attempts=5
      attempt=1
      while [ $attempt -le $max_attempts ]; do
        if GOVC_URL=${var.GOVC_URL} \
           GOVC_USERNAME=${var.GOVC_USERNAME} \
           GOVC_PASSWORD=${var.GOVC_PASSWORD} \
           GOVC_INSECURE=1 \
           govc vm.power -reset ${vsphere_virtual_machine.vm.name}; then
          break
        fi
        echo "Attempt $attempt failed. Retrying in 30 seconds..."
        sleep 30
        attempt=$((attempt + 1))
      done
      sleep 60
      GOVC_URL=${var.GOVC_URL} \
      GOVC_USERNAME=${var.GOVC_USERNAME} \
      GOVC_PASSWORD=${var.GOVC_PASSWORD} \
      GOVC_INSECURE=1 \
      govc snapshot.create -vm ${vsphere_virtual_machine.vm.name} "InitialSnapshot-$(date +%Y%m%d-%H%M%S)"
    EOT
  }
  lifecycle {
    create_before_destroy = true
  }
} 