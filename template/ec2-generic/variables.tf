variable "owner" {
    default = "peter.veentjer@scylladb.com"
}

variable "region" {
    default = "us-east-2"
}
 
variable "keypair_name" {
    default = "sso.pveentjer"
}

variable "public_key_location" {
    default = "../key.pub"
}

variable "private_key_location" {
    default = "../key"
}

# ============ cluster ===============

variable "cluster_size" {
    default = "1"
}

variable "cluster_instance_type" {
    default = "c5.2xlarge"
}

variable "cluster_name" {
    default = "sso.cluster pveentjer"
}

variable "cluster_user" {
    default = "centos"
}

variable "scylla_ami" {
    #  4.4.0
    default = "ami-0908bf554a8e333db"
}


# ============ prometheus instance ===============

variable "prometheus_instance_type" {
    default = "c5.xlarge"
}

variable "prometheus_ami" {
    # Ubuntu Server 18.04 
    default = "ami-0dd9f0e7df0f0a138"
}

# ============ prometheus instance ===============

variable "loadgenerator_instance_type" {
    default = "c5.4xlarge"
}

variable "loadgenerator_size" {
    default = "1"
}

variable "loadgenerator_ami" {
    default = "ami-0996d3051b72b5b2c"
}

variable "loadgenerator_user" {
    default = "ubuntu"
}

