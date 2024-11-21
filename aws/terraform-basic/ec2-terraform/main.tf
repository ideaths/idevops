terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 3.27"
    }
  }
  required_version = ">= 0.14.9"
}
provider "aws" {
  region  = "ap-southeast-1"
  profile = "default"
}

resource "aws_instance" "jumserver" {
  ami = "ami-0ac9397cab55f5044"
  instance_type = "t2.micro"
  tags = {
    Name = "jumserver"
  }
}