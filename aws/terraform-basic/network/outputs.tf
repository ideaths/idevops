#modules/network-layer/variables.tf
# VPC
output "vpc_duc" {
  value = "${aws.vpc.vpc_duc.*.id}"
}

# Subnet
output "subnet_id_private" {
  value = "${aws_subnet.subnet-private.*.id}"
}
output "subnet_id_public" {
  value = "${aws_subnet.subnet-public.*.id}"
}