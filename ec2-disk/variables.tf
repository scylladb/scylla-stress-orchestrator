
variable "region" {
    default = "us-east-2"
}

variable "keypair_name" {
    default = "pveentjer"
}

variable "cluster_size" {
    default = "1"
}

variable "cluster_instance_type" {
    default = "r5d.xlarge"
}

variable "cluster_name" {
    default = "cluster peter.v"
}

variable "availability_zone" {
    default = "us-east-2a"
}

variable "cluster_ami" {
    default = "ami-000f295fe8c032706"
}

variable "cluster_user" {
    default = "fedora"
}

variable "owner" {
    default = "peter.veentjer@scylladb.com"
}
