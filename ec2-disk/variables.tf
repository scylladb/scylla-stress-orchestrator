
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
    #default = "c5d.9xlarge"
    default = "i3.8xlarge"
    #default = "r5b.4xlarge"
}

variable "cluster_ami" {
    # fedora 33
    default = "ami-0054436646144eb33"
    
    # ubuntu
    #default = "ami-0996d3051b72b5b2c"
}

variable "cluster_user" {
    default = "fedora"
    #default = "ubuntu"
}

variable "cluster_name" {
    default = "cluster pveentjer"
}

variable ebs_block_device-device_name {
    default = "/dev/xvdb"    
}

variable ebs_block_device-volume_size {
    default = "3000"    
}

variable ebs_block_device-iops {
    default = null
}

variable ebs_block_device-volume_type {
    default = "gp3"    
}


    
