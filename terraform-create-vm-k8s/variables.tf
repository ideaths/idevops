variable "vm_name" {
  type        = string
  description = "Name of the virtual machine"
  default     = "vm_name"
}

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

variable "environment" {
  type        = string
  description = "Environment name (e.g., prod, dev, staging)"
  default     = "prod"
  validation {
    condition     = contains(["prod", "dev", "staging", "test"], var.environment)
    error_message = "Environment must be one of: prod, dev, staging, test."
  }
}

variable "project" {
  type        = string
  description = "Project name"
  default     = "k8s-cluster"
}
