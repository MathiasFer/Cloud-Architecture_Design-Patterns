resource "aws_vpc" "hub" {
  cidr_block           = var.hub_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "hub-vpc"
  }
}

resource "aws_subnet" "hub_subnet" {
  vpc_id            = aws_vpc.hub.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags = {
    Name = "hub-subnet-a"
  }
}

resource "aws_vpc" "spoke1" {
  cidr_block           = var.spoke1_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "spoke1-vpc"
  }
}

resource "aws_subnet" "spoke1_subnet" {
  vpc_id            = aws_vpc.spoke1.id
  cidr_block        = "10.1.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags = {
    Name = "spoke1-subnet-a"
  }
}

resource "aws_vpc" "spoke2" {
  cidr_block           = var.spoke2_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "spoke2-vpc"
  }
}

resource "aws_subnet" "spoke2_subnet" {
  vpc_id            = aws_vpc.spoke2.id
  cidr_block        = "10.2.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags = {
    Name = "spoke2-subnet-a"
  }
}

resource "aws_ec2_transit_gateway" "tgw" {
  description = "Transit Gateway interconnecting Hub and Spoke VPCs"
  tags = {
    Name = "main-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "hub" {
  transit_gateway_id = aws_ec2_transit_gateway.tgw.id
  vpc_id             = aws_vpc.hub.id
  subnet_ids         = [aws_subnet.hub_subnet.id]
  tags = {
    Name = "tgw-attachment-hub"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "spoke1" {
  transit_gateway_id = aws_ec2_transit_gateway.tgw.id
  vpc_id             = aws_vpc.spoke1.id
  subnet_ids         = [aws_subnet.spoke1_subnet.id]
  tags = {
    Name = "tgw-attachment-spoke1"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "spoke2" {
  transit_gateway_id = aws_ec2_transit_gateway.tgw.id
  vpc_id             = aws_vpc.spoke2.id
  subnet_ids         = [aws_subnet.spoke2_subnet.id]
  tags = {
    Name = "tgw-attachment-spoke2"
  }
}

resource "aws_route_table" "hub" {
  vpc_id = aws_vpc.hub.id
  tags = {
    Name = "hub-route-table"
  }
}

resource "aws_route" "hub_to_spoke1" {
  route_table_id         = aws_route_table.hub.id
  destination_cidr_block = var.spoke1_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.tgw.id
}

resource "aws_route" "hub_to_spoke2" {
  route_table_id         = aws_route_table.hub.id
  destination_cidr_block = var.spoke2_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.tgw.id
}

resource "aws_route_table_association" "hub" {
  subnet_id      = aws_subnet.hub_subnet.id
  route_table_id = aws_route_table.hub.id
}

resource "aws_route_table" "spoke1" {
  vpc_id = aws_vpc.spoke1.id
  tags = {
    Name = "spoke1-route-table"
  }
}

resource "aws_route" "spoke1_to_hub" {
  route_table_id         = aws_route_table.spoke1.id
  destination_cidr_block = "0.0.0.0/0"
  transit_gateway_id     = aws_ec2_transit_gateway.tgw.id
}

resource "aws_route_table_association" "spoke1" {
  subnet_id      = aws_subnet.spoke1_subnet.id
  route_table_id = aws_route_table.spoke1.id
}

resource "aws_route_table" "spoke2" {
  vpc_id = aws_vpc.spoke2.id
  tags = {
    Name = "spoke2-route-table"
  }
}

resource "aws_route" "spoke2_to_hub" {
  route_table_id         = aws_route_table.spoke2.id
  destination_cidr_block = "0.0.0.0/0"
  transit_gateway_id     = aws_ec2_transit_gateway.tgw.id
}

resource "aws_route_table_association" "spoke2" {
  subnet_id      = aws_subnet.spoke2_subnet.id
  route_table_id = aws_route_table.spoke2.id
}
