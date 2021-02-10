 

variable "cluster_size" {
    default = "2"
}

variable "loadgenerator_size" {
    default = "2"
}

variable "cluster_instance_type" {
    default = "c5.2xlarge"
}

variable "prometheus_instance_type" {
    default = "c5.xlarge"
}

variable "loadgenerator_instance_type" {
    default = "c5.4xlarge"
}

variable "scylla_ami" {
    default = "ami-02720bcdd160a5d8c"
}

variable "loadgenerator_ami" {
    default = "ami-0a0ad6b70e61be944"
}

variable "prometheus_ami" {
    # Ubuntu Server 18.04 
    default = "ami-0dd9f0e7df0f0a138"
}
