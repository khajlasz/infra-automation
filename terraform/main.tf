module "production_vpc" {
  source      = "./modules/custom_vpc"
  vpc_cidr    = "10.10.0.0/16"
  subnet_cidr = "10.10.1.0/24"
  vpc_name    = "enterprise-prod-vpc"
}

module "development_vpc" {
  source      = "./modules/custom_vpc"
  vpc_cidr    = "10.20.0.0/16"
  subnet_cidr = "10.20.1.0/24"
  vpc_name    = "enterprise-dev-vpc"
}

resource "aws_ec2_transit_gateway" "core_tgw" {
  description                     = "Main Enterprise Cloud Core Router"
  default_route_table_association = "enable"
  default_route_table_propagation = "enable"

  tags = {
    Name = "central-core-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "prod_attachment" {
  transit_gateway_id = aws_ec2_transit_gateway.core_tgw.id
  vpc_id             = module.production_vpc.vpc_id
  subnet_ids         = [module.production_vpc.subnet_id]

  tags = {
    Name = "prod-tgw-attachment"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "dev_attachment" {
  transit_gateway_id = aws_ec2_transit_gateway.core_tgw.id
  vpc_id             = module.development_vpc.vpc_id
  subnet_ids         = [module.development_vpc.subnet_id]

  tags = {
    Name = "dev-tgw-attachment"
  }
}