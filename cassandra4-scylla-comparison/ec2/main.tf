locals {
  yaml_configuration = yamldecode(file(var.yaml_configuration_path))

  deployment_name = "${terraform.workspace}-${random_id.deployment_id.hex}"

  region                = local.yaml_configuration["region"]
  availability_zone     = local.yaml_configuration["availability_zone"]
  cluster_size          = local.yaml_configuration["cluster_size"]
  cluster_instance_type = local.yaml_configuration["cluster_instance_type"]
  cluster_user          = local.yaml_configuration["cluster_user"]
  cluster_ami           = local.yaml_configuration["cluster_ami"]

  prometheus_instance_type = local.yaml_configuration["prometheus_instance_type"]
  prometheus_ami           = local.yaml_configuration["prometheus_ami"]

  loadgenerator_instance_type = local.yaml_configuration["loadgenerator_instance_type"]
  loadgenerator_size          = local.yaml_configuration["loadgenerator_size"]
  loadgenerator_user          = local.yaml_configuration["loadgenerator_user"]
  loadgenerator_ami           = local.yaml_configuration["loadgenerator_ami"]
}

resource "random_id" "deployment_id" {
  byte_length = 8
}

output "deployment_id" {
  value = random_id.deployment_id.hex
}

provider "aws" {
  profile = "default"
  region  = local.region
}

resource "aws_key_pair" "keypair" {
  key_name   = "sso-keypair-${local.deployment_name}"
  public_key = file(var.public_key_location)
}

# ==========cluster ==========================

resource "aws_security_group" "cluster-sg" {
  name        = "sso-cluster-sg-${local.deployment_name}"
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
    description = "NodeExporter"
    from_port   = 9100
    to_port     = 9100
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
    keep = "alive"
  }
}

resource "aws_instance" "cluster" {
  key_name          = aws_key_pair.keypair.key_name
  ami               = local.cluster_ami
  instance_type     = local.cluster_instance_type
  count             = local.cluster_size
  availability_zone = local.availability_zone

  tags = {
    Name = "sso-cluster-${count.index}-${local.deployment_name}"
    keep = "alive"
  }

  vpc_security_group_ids = [
    aws_security_group.cluster-sg.id
  ]

  connection {
    type        = "ssh"
    user        = local.cluster_user
    private_key = file(var.private_key_location)
    host        = self.public_ip
  }

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_type = "gp2"
    volume_size = 100
  }
}

output "cluster_public_ips" {
  value = aws_instance.cluster.*.public_ip
}

output "cluster_private_ips" {
  value = aws_instance.cluster.*.private_ip
}

# ========== prometheus ==========================

resource "aws_security_group" "prometheus-sg" {
  name        = "sso-prometheus-sg-${local.deployment_name}"
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
    keep = "alive"
  }
}

resource "aws_instance" "prometheus" {
  key_name          = aws_key_pair.keypair.key_name
  ami               = local.prometheus_ami
  instance_type     = local.prometheus_instance_type
  availability_zone = local.availability_zone

  tags = {
    Name = "sso-prometheus-${local.deployment_name}"
    keep = "alive"
  }

  vpc_security_group_ids = [
    aws_security_group.prometheus-sg.id
  ]

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_location)
    host        = self.public_ip
  }

  ebs_block_device {
      device_name = "/dev/sda1"
      volume_type = "gp3"
      volume_size = 384
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get -y -q update",
      "sudo apt-get -y install -q docker.io",
      "sudo apt-get -y -q update",
      "sudo apt-get -y install -q docker.io",
      "sudo usermod -aG docker $USER",
      "sudo systemctl enable docker",
      "wget -q https://github.com/scylladb/scylla-monitoring/archive/scylla-monitoring-3.6.3.tar.gz",
      "tar -xf scylla-monitoring-3.6.3.tar.gz",
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
    private_key = file(var.private_key_location)
    timeout     = "5m"
  }

  # FIXME: dc should not be hardcoded here!
  provisioner "file" {
    content = templatefile("scylla_server.yml.tpl", {
      ips     = aws_instance.cluster.*.private_ip
      cluster = "cluster1"
      dc      = "us-east-2"
    })
    destination = "scylla-monitoring-scylla-monitoring-3.6.3/prometheus/scylla_servers.yml"
  }

  provisioner "file" {
    content = templatefile("node_exporter.tpl", {
      ips     = aws_instance.cluster.*.private_ip
      cluster = "cluster1"
      dc      = "us-east-2"
    })
    destination = "scylla-monitoring-scylla-monitoring-3.6.3/prometheus/node_exporter"
  }

  provisioner "remote-exec" {
    inline = [
      "mkdir -p data",
      "cd scylla-monitoring-scylla-monitoring-3.6.3",
      "./kill-all.sh",
      "./start-all.sh -v 4.3 -d ../data",
    ]
  }
}

# ========== load generator ==========================

resource "aws_security_group" "loadgenerator-sg" {
  name        = "sso-loadgenerator-sg-${local.deployment_name}"
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
    keep = "alive"
  }
}

resource "aws_instance" "loadgenerator" {
  key_name          = aws_key_pair.keypair.key_name
  ami               = local.loadgenerator_ami
  instance_type     = local.loadgenerator_instance_type
  count             = local.loadgenerator_size
  availability_zone = local.availability_zone

  tags = {
    Name = "sso-loadgenerator-${count.index}-${local.deployment_name}",
    keep = "alive"
  }

  vpc_security_group_ids = [
    aws_security_group.loadgenerator-sg.id
  ]
}

output "loadgenerator_public_ips" {
  value = aws_instance.loadgenerator.*.public_ip
}

output "loadgenerator_private_ips" {
  value = aws_instance.loadgenerator.*.private_ip
}
