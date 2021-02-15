
provider "aws" {
    profile = "default"
    region = var.region
}

resource "aws_key_pair" "keypair" {
    key_name   = var.keypair_name
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
        Owner = var.owner
    }
}

resource "aws_instance" "cluster" {
    key_name          = aws_key_pair.keypair.key_name
    ami               = var.cluster_ami
    instance_type     = var.cluster_instance_type
    count             = var.cluster_size
    availability_zone = var.availability_zone

    tags = {
        Name  = var.cluster_name
        Owner = var.owner
    }

    vpc_security_group_ids = [
        aws_security_group.cluster-sg.id
    ]

    connection {
        type        = "ssh"
        user        = var.cluster_user
        private_key = file("../key")
        host        = self.public_ip
        timeout     = "8m"
    }
  
    # root disk
    root_block_device {
        volume_size           = "20"
        volume_type           = "gp2"
        encrypted             = true
        delete_on_termination = true
    }
  
    ebs_block_device {
        device_name = "/dev/sdd"
        volume_size = "10"
        volume_type = "standard"
        delete_on_termination = true
    }
    
    provisioner "remote-exec" {
        inline = [
            "sudo mkfs -t xfs /dev/sdd",
            "sudo mkdir /data",
            "sudo mount /dev/sdx /data",
            "sudo chown -R ec2-user /data",
            "sudo chmod -R g+rw /data"
        ]
    }
}

output "cluster_public_ips" {
    value = aws_instance.cluster.*.public_ip
}

output "cluster_private_ips" {
    value = aws_instance.cluster.*.private_ip
}
