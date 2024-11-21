provider "aws" {
  region  = "${var.region}"
  profile = "default"
}
resource "aws_vpc" "vpc_duc" {
  cidr_block = "${var.vpc_icdr}"
  tags = {
    Name = "vpc-${var.env}"
    Stage = "${var.env}"
  }
}
