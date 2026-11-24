terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_security_group" "migrated_ec2_sg" {
  name        = "lift-and-shift-migrated-sg"
  description = "Security group for lifted on-premise server on AWS"
  vpc_id      = "vpc-spoke1"

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "migrated_onprem_server" {
  ami                  = "ami-0c55b159cbfafe1f0"
  instance_type        = "m5.large"
  subnet_id            = "subnet-spoke1-private"
  vpc_security_group_ids = [
    aws_security_group.migrated_ec2_sg.id
  ]

  root_block_device {
    volume_size           = 100
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name              = "lift-and-shift-app-server"
    MigrationStrategy = "Lift-and-Shift"
    SourcePlatform    = "On-Premises VMware"
  }
}
