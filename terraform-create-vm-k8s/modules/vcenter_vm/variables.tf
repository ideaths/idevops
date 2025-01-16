variable "vm_name" {
  type        = string
  description = "The name of the virtual machine"
  validation {
    condition     = length(var.vm_name) > 2 && length(var.vm_name) <= 80
    error_message = "VM name must be between 3 and 80 characters."
  }
}

variable "resource_pool_id" {
  type        = string
  description = "The resource pool ID for the VM"
}

variable "datastore_id" {
  type        = string
  description = "The datastore ID where the VM will be stored"
}

variable "network_id" {
  type        = string
  description = "The network ID the VM will connect to"
}

variable "guest_id" {
  type        = string
  description = "The guest OS ID for the VM"
}

variable "num_cpus" {
  type        = number
  description = "Number of CPUs for the VM"
  validation {
    condition     = var.num_cpus > 0 && var.num_cpus <= 32
    error_message = "CPU cores must be between 1 and 32."
  }
}

variable "memory" {
  type        = number
  description = "Memory size (in MB) for the VM"
  validation {
    condition     = var.memory >= 1024 && var.memory <= 65536
    error_message = "Memory must be between 1024MB and 65536MB."
  }
}

variable "disk_size" {
  type        = number
  description = "Disk size (in GB) for the VM"
  default     = 50
  validation {
    condition     = var.disk_size >= 20
    error_message = "Disk size must be at least 20GB."
  }
}

variable "adapter_type" {
  type        = string
  description = "The network adapter type for the VM"
  default     = "vmxnet3"
  validation {
    condition     = contains(["vmxnet3", "e1000", "e1000e"], var.adapter_type)
    error_message = "Adapter type must be one of: vmxnet3, e1000, e1000e."
  }
}

variable "eagerly_scrub" {
  type        = bool
  description = "Whether the disk is eagerly scrubbed (recommended for production)"
  default     = false
}

variable "thin_provisioned" {
  type        = bool
  description = "Whether the disk is thin provisioned (recommended for development)"
  default     = true
}

variable "template_uuid" {
  type        = string
  description = "The UUID of the template VM to clone"
}

variable "ipv4_address" {
  type        = string
  description = "IP Address for the VM"
  validation {
    condition     = can(regex("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$", var.ipv4_address))
    error_message = "Invalid IP address format."
  }
}

variable "ipv4_netmask" {
  type        = number
  description = "Netmask for the VM (in bits)"
  default     = 24
  validation {
    condition     = var.ipv4_netmask >= 8 && var.ipv4_netmask <= 32
    error_message = "Netmask must be between 8 and 32."
  }
}

variable "ipv4_gateway" {
  type        = string
  description = "Gateway IP address for the VM"
  validation {
    condition     = can(regex("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$", var.ipv4_gateway))
    error_message = "Invalid gateway IP address format."
  }
}

variable "vm_hostname" {
  type        = string
  description = "Hostname for the VM"
  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$", var.vm_hostname))
    error_message = "Invalid hostname format."
  }
}

variable "domain" {
  type        = string
  description = "Domain name for the VM"
  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,}$", var.domain))
    error_message = "Invalid domain name format."
  }
}

variable "dns_servers" {
  type        = list(string)
  description = "List of DNS servers"
  default     = ["10.0.6.3"]
  validation {
    condition     = length(var.dns_servers) > 0
    error_message = "At least one DNS server must be specified."
  }
}

# vSphere credentials
variable "GOVC_URL" {
  type        = string
  description = "vSphere server URL"
  sensitive   = true
}

variable "GOVC_USERNAME" {
  type        = string
  description = "vSphere username"
  sensitive   = true
}

variable "GOVC_PASSWORD" {
  type        = string
  description = "vSphere password"
  sensitive   = true
}