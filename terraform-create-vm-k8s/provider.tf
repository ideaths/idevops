provider "vsphere" {
  user                 = var.GOVC_USERNAME
  password             = var.GOVC_PASSWORD
  vsphere_server       = var.GOVC_URL
  allow_unverified_ssl = true
}