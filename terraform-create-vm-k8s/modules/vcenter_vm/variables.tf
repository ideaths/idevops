variable "vm_name" {
  type        = string
  description = "The name of the virtual machine"
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

variable "template_name" {
  type        = string
  description = "The template name for cloning the VM"
  default     = "template-ubuntu-24"
}

variable "guest_id" {
  type        = string
  description = "The guest OS ID for the VM"
}

variable "datacenter_id" {
  type        = string
  description = "The ID of the datacenter where the VM will be deployed"
  default     = "Home"
}

variable "num_cpus" {
  type        = number
  description = "Number of CPUs for the VM"
}

variable "memory" {
  type        = number
  description = "Memory size (in MB) for the VM"
}

variable "disk_size" {
  type        = number
  description = "Disk size (in GB) for the VM"
  default     = 50
}

variable "adapter_type" {
  type        = string
  description = "The network adapter type for the VM"
  default     = "vmxnet3"  # Set a default value if suitable
}
variable "eagerly_scrub" {
  type        = bool
  description = "Whether the disk is eagerly scrubbed"
  default     = false
}

variable "thin_provisioned" {
  type        = bool
  description = "Whether the disk is thin provisioned"
  default     = true
}
variable "template_uuid" {
  type        = string
  description = "The UUID of the template VM to clone"
}

variable "ipv4_address" {
  description = "IP Address for the VM"
  type        = string
}

variable "ipv4_netmask" {
  description = "Netmask for the VM"
  type        = number
  default     = 24
}

variable "ipv4_gateway" {
  description = "Gateway for the VM"
  type        = string
}
variable "vm_hostname" {
  description = "Hostname for the VM"
  type        = string
}

variable "domain" {
  description = "Domain name for the VM"
  type        = string
}


variable "GOVC_URL" {}
variable "GOVC_USERNAME" {}
variable "GOVC_PASSWORD" {}