resource "aws_vpc" "vpc_engine" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = {
    Name = var.vpc_name
  }
}

resource "aws_subnet" "private_subnet" {
    vpc_id          = aws_vpc.vpc_engine.id
    cidr_block      = var.subnet_cidr
    availability_zone = "eu-central-1a"

    tags = {
        Name = "${var.vpc_name}-private-subnet"
    }
}