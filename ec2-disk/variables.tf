
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
    default = "peter.veentjer"
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
    #default = "i3.8xlarge"
    default = "r5b.4xlarge"
}

variable "cluster_ami" {
    # centos us-east-2
    #default = "ami-01e36b7901e884a10"
    
    # rhel us-east-2
    default = "ami-03d64741867e7bb94"
    
    # fedora 33
    #default = "ami-0054436646144eb33"
    
    #ubuntu
    #default = "ami-0996d3051b72b5b2c"
    
    # centos 7
    #default = "ami-01e36b7901e884a10"
    
    # rhel 8
    #default = "ami-03d64741867e7bb94"
}

variable "cluster_user" {
    #default = "fedora"
    #default = "ubuntu"
    default = "centos"
    #default = "ec2-user"
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
    default = "64000"
}

variable ebs_block_device-volume_type {
    default = "io1"    
}


    
