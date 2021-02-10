
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

    # list of ports https://docs.scylladb.com/operating-scylla/admin/

    ingress {
        description = "SSH"
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "CQL"
        from_port   = 9042
        to_port     = 9042
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "SSL_CQL"
        from_port   = 9142
        to_port     = 9142
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "RPC"
        from_port   = 7000
        to_port     = 7000
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "SSL RPC"
        from_port   = 7001
        to_port     = 7001
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "JMX"
        from_port   = 7199
        to_port     = 7199
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "REST"
        from_port   = 10000
        to_port     = 10000
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "Prometheus"
        from_port   = 9180
        to_port     = 9180
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
  
    ingress {
        description = "Thrift"
        from_port   = 9160
        to_port     = 9160
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
    ami             = var.scylla_ami
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

resource "null_resource" "cluster" {

    triggers = {
        cluster_instance_ids = join(",", aws_instance.cluster.*.id)
    }

    connection {
        type        = "ssh"
        host        = element(aws_instance.cluster.*.public_ip, count.index)
        user        = "centos"
        private_key = file("../key")
        timeout     = "8m"
    }

    provisioner "remote-exec" {
        inline = [
            "sudo scylla_io_setup",
            "sudo sed -i \"s/cluster_name:.*/cluster_name: cluster1/g\" /etc/scylla/scylla.yaml",
            "sudo sed -i \"s/seeds:.*/seeds: ${aws_instance.cluster[0].private_ip} /g\" /etc/scylla/scylla.yaml",
            "sudo systemctl start scylla-server",
        ]
    }
  
    count = var.cluster_size
}

output "cluster_public_ips" {
    value = aws_instance.cluster.*.public_ip
}

output "cluster_private_ips" {
    value = aws_instance.cluster.*.private_ip
}

# ========== prometheus ==========================

resource "aws_security_group" "prometheus-sg" {
    name        = "prometheus-sg"
    description = "Security group for Prometheus"

    ingress {
        description = "SSH" 
        from_port   = 22 
        to_port     = 22 
        protocol    = "tcp" 
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "prometheus"
        from_port   = 9090
        to_port     = 9090
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    
    ingress {
        description = "x"
        from_port   = 3000
        to_port     = 3000
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "Alert Manager"
        from_port   = 9003
        to_port     = 9003
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

resource "aws_instance" "prometheus" {
    key_name        = aws_key_pair.keypair.key_name
    ami             = var.prometheus_ami
    instance_type   = var.prometheus_instance_type
    count           = 1

    tags = {
        Name = "prometheus peter.v",
        Owner = "peter.veentjer@scylladb.com"
    }

    vpc_security_group_ids = [
        aws_security_group.prometheus-sg.id
    ]

    connection {
        type        = "ssh"
        user        = "ubuntu"
        private_key = file("../key")
        host        = self.public_ip
    }
    
    provisioner "remote-exec" {
        inline = [
            "sudo apt-get -y -q update",     
            "sudo apt-get -y install -q docker.io",   
            "sudo usermod -aG docker $USER",
            "sudo systemctl enable docker",
            "wget -q https://github.com/scylladb/scylla-monitoring/archive/branch-3.4.tar.gz",
            "tar -xf branch-3.4.tar.gz",
            "sudo systemctl restart docker",
        ]
    }
}

output "prometheus_public_ip" {
    value = aws_instance.prometheus.*.public_ip
}

# update prometheus
resource "null_resource" "configure-prometheus" {

    triggers = {
        cluster_instance_ids = join(",", aws_instance.cluster.*.id)
    }
    
    connection {
        type        = "ssh"
        host        = element(aws_instance.prometheus.*.public_ip, 0)
        user        = "ubuntu"
        private_key = file("../key")
        timeout     = "5m"
    }
    
    provisioner "file" {
        content     = templatefile("scylla_server.yml.tpl", {
            ips       = aws_instance.cluster.*.private_ip
            cluster   = "cluster1"
            dc        = "us-east-2"
        })
        destination = "scylla-monitoring-branch-3.4/prometheus/scylla_servers.yml"
    }

    provisioner "remote-exec" {
        inline = [
            "touch has_run",
            "cd scylla-monitoring-branch-3.4",
            "./kill-all.sh",
            "./start-all.sh",
        ]
    }
}

# ========== load generator ==========================

resource "aws_security_group" "loadgenerator-sg" {
    name        = "loadgenerator-sg"
    description = "Security group for the loadgenerator"

    ingress {
        description = "SSH" 
        from_port   = 22 
        to_port     = 22 
        protocol    = "tcp" 
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        description = "cassandra-stress-daemon"
        from_port   = 2159
        to_port     = 2159
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

resource "aws_instance" "loadgenerator" {
    key_name          = aws_key_pair.keypair.key_name
    ami               = var.loadgenerator_ami
    instance_type     = var.loadgenerator_instance_type
    count             = var.loadgenerator_size


    tags = {
        Name = "load generator peter.v",
        Owner = "peter.veentjer@scylladb.com"
    }

    vpc_security_group_ids = [
        aws_security_group.loadgenerator-sg.id
    ]

    connection {
        type        = "ssh"
        user        = "ec2-user"
        private_key = file("../key")
        host        = self.public_ip
    }
}

output "loadgenerator_public_ips" {
    value = aws_instance.loadgenerator.*.public_ip
}

output "loadgenerator_private_ips" {
    value = aws_instance.loadgenerator.*.private_ip
}




