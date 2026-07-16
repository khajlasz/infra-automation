output "vpc_id" {
    value = aws_vpc.vpc_engine.id
}

output "subnet_id" {
    value = aws_subnet.private_subnet.id
}