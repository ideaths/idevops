# Public Subnet
resource "aws_subnet" "subnet-public" {
  count = "1"
  vpc_id = "${aws_vpc.vpc_duc.id}"
  cidr_block = "${var.subnet_public_cidrs[count.index]}"
  map_public_ip_on_launch = "true"
  tags = {
    Name = "subnet-public-${var.env}-${count.index}"
    Stage = "${var.env}"
  }
}

#Private Subnet
resource "aws_subnet" "subnet-private" {
  count = "1"
  vpc_id = "${aws_vpc.vpc_duc.id}"
  cidr_block = "${var.subnet_private_cidrs[count.index]}"
  map_public_ip_on_launch = "true"
  tags = {
    Name = "subnet-private-${var.env}-${count.index}"
    Stage = "${var.env}"
  }
}
#############
resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = "${aws_vpc.vpc_duc.id}"
  tags = {
    Name = "internet-gateway-${var.env}"
    Stage = "${var.env}"
  }
}
resource "aws_route_table" "route_table_public" {
  vpc_id = "${aws_vpc.vpc_duc.id}"
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.internet_gateway.id}"
  }
  tags = {
    Name = "route-table-public-${var.env}"
    Stage = "${var.env}"
  }
}
resource "aws_route_table_association" "route_table_association_public" {
  route_table_id = "${aws_route_table.route_table_public.id}"
  subnet_id = "${aws_subnet.subnet-public.*.id[count.index]}"
  count = "${length(aws_subnet.subnet-public)}"
}


#############
resource "aws_eip" "nat_eip_private" {
  vpc = true
    tags = {
    Name = "eip-nat-${var.env}"
    Stage = "${var.env}"
  }
}
resource "aws_nat_gateway" "aws_nat_gateway" {
    count = "${length(aws_subnet.subnet-private)}"
    allocation_id = "${aws_eip.nat_eip_private.id}"
    subnet_id = "${aws_subnet.subnet-private.*.id[count.index]}"
    tags = {
      Name = "nat-gateway-${var.env}"
      Stage = "${var.env}"
    }
}

resource "aws_route_table" "route_table_private" {
  vpc_id = "${aws_vpc.vpc_duc.id}"
  count = "${length(aws_nat_gateway.aws_nat_gateway)}"
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_nat_gateway.aws_nat_gateway.*.id[count.index]}"
  }
  tags = {
    Name = "route-table-private-${var.env}"
    Stage = "${var.env}"
  }
}
resource "aws_route_table_association" "route_table_association_private" {
  route_table_id = "${aws_route_table.route_table_private.*.id[count.index]}"
  subnet_id = "${aws_subnet.subnet-private.*.id[count.index]}"
  count = "${length(aws_subnet.subnet-private)}"
}