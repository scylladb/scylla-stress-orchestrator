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
user                = "ec2-user"
basename            = "storage/junk-i3.4xlarge/"

def make_data_dir(ip, dev, dir):
    print("Creating and mounting file system: started")
    ssh = Ssh(ip, user, ssh_options)
    ssh.run("lsblk")
    ssh.run(f"sudo umount {dev} || true")
    ssh.run(f"sudo rm -fr {dir}")
    ssh.run(f"sudo mkfs -t xfs {dev}")
    ssh.run(f"sudo mkdir {dir}")
    ssh.run(f"sudo mount {dev} {dir}")
    ssh.run(f"sudo chown -R {user} {dir}")
    ssh.run(f"sudo chmod -R g+rw {dir}")
    ssh.run("lsblk")
    print("Creating and mounting file system: done")
    
    
def run_instanceStore_DiskExplorer(name, dev):
    dir             = "/mnt/data"
    iteration       = Iteration(f"{basename}/{name}", "centos-raid")
    environment     = common.load_yaml('environment.yml')
    public_ips      = environment['cluster_public_ips']
    
    common.collect_ec2_metadata(public_ips, user, ssh_options, iteration.dir)
    
    ssh = Ssh(public_ips[0], user, ssh_options)
    ssh.run("lsblk")
    ssh.run("sudo yum -y install epel-release")
    ssh.run("sudo curl -o /etc/yum.repos.d/scylla.repo -L http://repositories.scylladb.com/scylla/repo/603fc559-4518-4f8e-8ceb-2851dec4ab23/centos/scylladb-4.3.repo")
    ssh.run("sudo yum -y install scylla")
    ssh.run("sudo scylla_raid_setup --disk /dev/nvme0n1,/dev/nvme1n1")
        
    make_data_dir(public_ips[0], "/dev/md0", dir)
   
    diskExplorer = DiskExplorer(public_ips, user, ssh_options)
    diskExplorer.install()
    #diskExplorer.run(f"-o diskplorer -d {dir} -m 1000")
    diskExplorer.download(iteration.dir)


def run_ebs_DiskExplorer(name, dev):
    dir             = "/mnt/data"
    iteration       = Iteration(f"{basename}/{name}", "centos-raid")
    environment     = common.load_yaml('environment.yml')
    public_ips      = environment['cluster_public_ips']

    common.collect_ec2_metadata(public_ips, user, ssh_options, iteration.dir)
    
    ssh = Ssh(public_ips[0], user, ssh_options)
    ssh.run("sudo yum -y install epel-release")
    ssh.run("sudo curl -o /etc/yum.repos.d/scylla.repo -L http://repositories.scylladb.com/scylla/repo/603fc559-4518-4f8e-8ceb-2851dec4ab23/centos/scylladb-4.3.repo")
    ssh.run("sudo yum -y install scylla")
    ssh.run("lsblk")
    ssh.run("sudo scylla_raid_setup --disk /dev/xvdb,/dev/xvdc,/dev/xvdd,/dev/xvde")
    
    make_data_dir(public_ips[0], "/dev/md0", dir)
    diskExplorer = DiskExplorer(public_ips, user, ssh_options)
    diskExplorer.install()
    #diskExplorer.run(f"-o diskplorer -d {dir}")
    diskExplorer.download(iteration.dir)


terraform.apply(terraform_plan)

run_instanceStore_DiskExplorer("instance-store-raid/", "/dev/nvme1n1")

#run_ebs_DiskExplorer("io2-raid/", "/dev/nvme1n1") 

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
