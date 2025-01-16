provider "vsphere" {
  user                 = var.GOVC_USERNAME
  password             = var.GOVC_PASSWORD
  vsphere_server       = var.GOVC_URL
  allow_unverified_ssl = true

  # Add connection settings
  vim_keep_alive = 300
  api_timeout    = 60
  persist_session = true
}

provider "null" {}