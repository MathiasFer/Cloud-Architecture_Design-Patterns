variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "hub_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "spoke1_cidr" {
  type    = string
  default = "10.1.0.0/16"
}

variable "spoke2_cidr" {
  type    = string
  default = "10.2.0.0/16"
}
