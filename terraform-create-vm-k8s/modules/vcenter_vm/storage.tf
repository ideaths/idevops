locals {
  disk = [{
    label            = "disk0"
    size             = var.disk_size
    eagerly_scrub    = var.eagerly_scrub
    thin_provisioned = var.thin_provisioned
  }]
}
