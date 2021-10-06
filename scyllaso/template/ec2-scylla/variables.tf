variable "owner" {
    default = "sso.<resourceid>"
}

variable "placement_group_name" {
    default = "sso.pg-<resourceid>"
}

variable "region" {
    default = "us-east-2"
}
 
variable "keypair_name" {
    default = "sso.keypair-<resourceid>"
}

variable "public_key_location" {
    default = "../key.pub"
}

variable "private_key_location" {
    default = "../key"
}

# ============ Scylla Cluster ===============

variable "cluster_size" {
    default = "1"
}

variable "cluster_sg_name" {
    default = "sso.cluster-sg-<resourceid>"
}

variable "cluster_instance_type" {
    default = "i3.2xlarge"
}

variable "cluster_name" {
    default = "sso.cluster-<resourceid>"
}

variable "cluster_user" {
    default = "centos"
}

variable "scylla_ami" {
    # When a centos image is used, the extra packages are not installed.
    # So you can't install tools like htop, hwloc etc.
    # Check the following link to enable to extra packages
    # https://fedoraproject.org/wiki/EPEL

    #  4.4.4
    default = "ami-0c0575324d81db474"
}


# ============ Prometheus instance ===============

variable "prometheus_name" {
    default = "sso.prometheus-<resourceid>"
}

variable "prometheus_sg_name" {
    default = "sso.prometheus-sg-<resourceid>"
}

variable "prometheus_instance_type" {
    default = "c5.xlarge"
}

variable "prometheus_ami" {
    # Ubuntu Server 18.04 
    default = "ami-0dd9f0e7df0f0a138"
}

variable "scylla_monitoring_version" {
    default = "3.8.2"
}

# ============ Load Generators  ===============

variable "loadgenerator_instance_type" {
    default = "c5.4xlarge"
}

variable "loadgenerator_name" {
    default = "sso.loadgenerator-<resourceid>"
}

variable "loadgenerator_sg_name" {
    default = "sso.loadgenerator-sg-<resourceid>"
}

variable "loadgenerator_size" {
    default = "2"
}

variable "loadgenerator_ami" {
    default = "ami-0996d3051b72b5b2c"
}

variable "loadgenerator_user" {
    default = "ubuntu"
}

