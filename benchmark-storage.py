#!/bin/python3

import common
import terraform
from common import CassandraStress
from common import Iteration
from common import DiskExplorer
from common import Ssh
from common import Fio


properties          = common.load_yaml('properties.yml')
ssh_options         = properties['ssh_options']
terraform_plan      = properties.get('terraform_plan')
user                = "fedora"
basename            = "storage/i3.8xlarge/"

def make_data_dir(ip, dev, dir):
    print("Creating and mounting file system: started")
    ssh = Ssh(ip, user, ssh_options)
    ssh.run("lsblk")
    ssh.run(f"sudo mkfs -t xfs {dev}")
    ssh.run(f"sudo mkdir {dir}")
    ssh.run(f"sudo mount {dev} {dir}")
    ssh.run(f"sudo chown -R {user} {dir}")
    ssh.run(f"sudo chmod -R g+rw {dir}")
    ssh.run("lsblk")
    print("Creating and mounting file system: done")
    
def run_diskExplorer(name, dev):
    dir             = "/mnt/data"
    iteration       = Iteration(f"{basename}/{name}")
    environment     = common.load_yaml('environment.yml')
    public_ips      = environment['cluster_public_ips']
    
    make_data_dir(public_ips[0], dev, dir)   
   
    diskExplorer = DiskExplorer(public_ips, user, ssh_options)
    diskExplorer.install()
    diskExplorer.run(f"-o diskplorer -d {dir}")
    diskExplorer.download(iteration.dir)


terraform.apply(terraform_plan)
run_diskExplorer("instance-store/", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)

#terraform.apply(terraform_plan,f'-var="ebs_block_device-volume_size=3000" -var="ebs_block_device-volume_type=gp2" ')
#run_diskExplorer("ebs-gp2", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)
 
#terraform.apply(terraform_plan,f'-var="ebs_block_device-volume_size=3000" -var="ebs_block_device-volume_type=gp3" ')
#run_diskExplorer("ebs-gp3", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)

#terraform.apply(terraform_plan,f'-var="ebs_block_device-volume_size=3000" -var="ebs_block_device-volume_type=gp3" -var="ebs_block_device-iops=16000"')
#run_diskExplorer("ebs-gp3-iops", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)

#terraform.apply(terraform_plan,f'-var="ebs_block_device-volume_size=3000" -var="ebs_block_device-volume_type=io1" -var="ebs_block_device-iops=64000" ')
#run_diskExplorer("ebs-io1", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)
    
#terraform.apply(terraform_plan,f'-var="ebs_block_device-volume_size=12000" -var="ebs_block_device-volume_type=io2" -var="ebs_block_device-iops=64000" ')
#run_diskExplorer("ebs-io2", "/dev/nvme1n1") 
#terraform.destroy(terraform_plan)



#fio = Fio(public_ips, user, ssh_options)
#fio.install()
#fio.run(f"--filename={dev} --direct=1 --rw=randread --bs=4k --ioengine=libaio --iodepth=256 --runtime=120 --numjobs=4 --time_based --group_reporting --name=iops-test-job --eta-newline=1 --readonly --output bla")
#fio.download(iteration.dir)
