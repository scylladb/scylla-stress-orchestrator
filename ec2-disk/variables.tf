
variable "region" {
    default = "us-east-2"
}

variable "availability_zone" {
    default = "us-east-2a"
}

variable "owner" {
    default = "peter.veentjer@scylladb.com"
}

variable "keypair_name" {
    default = "blibli"
}

variable "public_key_location" {
    default = "../key.pub"
}

variable "private_key_location" {
    default = "../key"
}

variable "cluster_size" {
    default = "1"
}

variable "cluster_instance_type" {
    default = "r5b.2xlarge"
}

variable "cluster_ami" {
    default = "ami-001aa9e3581d595dc"
}

variable "cluster_user" {
    default = "fedora"
}

variable "cluster_name" {
    default = "cluster pveentjer"
}

