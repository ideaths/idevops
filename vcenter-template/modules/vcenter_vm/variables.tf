variable "vm_name" {
  type        = string
  description = "Name of the virtual machine"
}

variable "resource_pool_id" {
  type        = string
  description = "ID of the resource pool"
}

variable "datastore_id" {
  type        = string
  description = "ID of the datastore"
}

variable "num_cpus" {
  type        = number
  description = "Number of CPUs for the VM"
  default     = 2
}

variable "memory" {
  type        = number
  description = "Memory size (MB)"
  default     = 4096
}

variable "guest_id" {
  type        = string
  description = "Guest OS ID"
  default     = "ubuntu64Guest"
}

variable "network_id" {
  type        = string
  description = "Network ID for the VM"
}

variable "adapter_type" {
  type        = string
  description = "Adapter type for network"
  default     = "vmxnet3"
}

variable "disk_size" {
  type        = number
  description = "Disk size (GB)"
  default     = 50
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

variable "cdrom_datastore_id" {
  type        = string
  description = "Datastore ID for the CD-ROM"
}

variable "cdrom_path" {
  type        = string
  description = "Path to the ISO"
}

variable "boot_delay" {
  type        = number
  description = "Boot delay in milliseconds"
  default     = 5000
}

variable "wait_for_guest_net_timeout" {
  type        = number
  description = "Timeout for waiting for guest network"
  default     = 0
}