
provider "aws" {
    profile = "default"
    region = var.region
}

resource "aws_key_pair" "keypair" {
    key_name   = var.keypair_name
    public_key = file(var.public_key_location)
}

# ==========cluster ==========================

resource "aws_security_group" "cluster-sg1" {
    name        = "cluster-sg1"
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
        aws_security_group.cluster-sg1.id
    ]
  
    # read following if devices don't show up
    # https://stackoverflow.com/questions/22816878/my-mounted-ebs-volume-is-not-showing-up
    ebs_block_device {
        device_name             = "/dev/xvdb"
        volume_size             = var.ebs_block_device-volume_size
        iops                    = var.ebs_block_device-iops
        volume_type             = var.ebs_block_device-volume_type
        delete_on_termination   = true
    }
    
    ebs_block_device {
        device_name             = "/dev/xvdd"
        volume_size             = var.ebs_block_device-volume_size
        iops                    = var.ebs_block_device-iops
        volume_type             = var.ebs_block_device-volume_type
        delete_on_termination   = true
    }
 
    ebs_block_device {
        device_name             = "/dev/xvde"
        volume_size             = var.ebs_block_device-volume_size
        iops                    = var.ebs_block_device-iops
        volume_type             = var.ebs_block_device-volume_type
        delete_on_termination   = true
    }
    
    ebs_block_device {
        device_name             = "/dev/xvdf"
        volume_size             = var.ebs_block_device-volume_size
        iops                    = var.ebs_block_device-iops
        volume_type             = var.ebs_block_device-volume_type
        delete_on_termination   = true
    }

    #connection {
    #    type        = "ssh"
    #    user        = var.cluster_user
    #    private_key = file(var.private_key_location)
    #    host        = self.public_ip
    #    agent       = false
    #    timeout     = "60m"
    #}
   
    #provisioner "remote-exec" {
    #       inline = [
    #        "ls"
    #        #"sudo mkfs -t xfs /dev/nvme1n1",
    #        #"sudo mkdir /data",
    #        #"sudo mount /dev/nvme1n1 /data",
    #        #"sudo chown -R ec2-user /data",
    #        #"sudo chmod -R g+rw /data"
    #    ]
    #}
}

output "cluster_public_ips" {
    value = aws_instance.cluster.*.public_ip
}

output "cluster_private_ips" {
    value = aws_instance.cluster.*.private_ip
}
