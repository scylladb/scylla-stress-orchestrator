
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
    default = "banana"
}

variable "public_key_location" {
    default = "../key.pub"
}

variable "private_key_location" {
    default = "../key.pem"
}

variable "cluster_size" {
    default = "1"
}

variable "cluster_instance_type" {
    default = "r5d.xlarge"
}

variable "cluster_ami" {
    default = "ami-000f295fe8c032706"
}

variable "cluster_user" {
    default = "core"
}

variable "cluster_name" {
    default = "cluster pveentjer"
}

