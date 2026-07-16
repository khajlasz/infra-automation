variable "vpc_cidr" {
  type        = string
  description = "The main CIDR block for the VPC"
}

variable "vpc_name" {
    type        = string
    description = "The name tag associated to the VPC"
}

variable "subnet_cidr" {
    type        = string
    description = "The CIDR for the primary internal private subnet"
}