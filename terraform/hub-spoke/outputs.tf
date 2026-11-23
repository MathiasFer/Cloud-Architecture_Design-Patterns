output "transit_gateway_id" {
  value = aws_ec2_transit_gateway.tgw.id
}

output "hub_vpc_id" {
  value = aws_vpc.hub.id
}

output "spoke1_vpc_id" {
  value = aws_vpc.spoke1.id
}

output "spoke2_vpc_id" {
  value = aws_vpc.spoke2.id
}
