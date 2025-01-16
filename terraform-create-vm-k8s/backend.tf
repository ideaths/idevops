terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
  # Hoặc sử dụng S3/Azure/GCS backend
  # backend "s3" {
  #   bucket = "terraform-state"
  #   key    = "k8s-cluster/terraform.tfstate"
  #   region = "ap-southeast-1"
  # }
} 