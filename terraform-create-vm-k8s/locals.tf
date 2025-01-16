locals {
  # Common tags
  common_tags = {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "Terraform"
    Owner       = "DevOps"
  }

  # Network configuration
  network_config = {
    subnet_mask = "255.255.255.0"
    dns_suffix  = "idevops.io.vn"
  }

  # VM type configurations
  vm_types = {
    master = {
      cpu    = 4
      memory = 4096
    }
    worker = {
      cpu    = 8
      memory = 8192
    }
    infra = {
      cpu    = 4
      memory = 8192
    }
  }
} 