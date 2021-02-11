
provider "aws" {
    profile = "default"
    region = "us-east-2"
}

resource "aws_key_pair" "keypair" {
    key_name   = "scylla.kp"
    public_key = file("../key.pub")
}

# ==========cluster ==========================

resource "aws_security_group" "cluster-sg" {
    name        = "cluster-sg"
    description = "Security group for the cluster"

    ingress {
        description = "SSH"
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "terraform",
        Owner = "peter.veentjer@scylladb.com"
    }
}

resource "aws_instance" "cluster" {
    key_name        = aws_key_pair.keypair.key_name
    ami             = var.cluster_ami
    instance_type   = var.cluster_instance_type
    count           = var.cluster_size

    tags = {
        Name = "cluster peter.v",
        Owner = "peter.veentjer@scylladb.com"
    }

    vpc_security_group_ids = [
        aws_security_group.cluster-sg.id
    ]

    connection {
        type        = "ssh"
        user        = "centos"
        private_key = file("../key")
        host        = self.public_ip
    }
  
    ebs_block_device {
        device_name = "/dev/sda1"
        volume_type = "io1"
        iops = "20000"
        volume_size = 1000
    }
}

output "cluster_public_ips" {
    value = aws_instance.cluster.*.public_ip
}

output "cluster_private_ips" {
    value = aws_instance.cluster.*.private_ip
}
