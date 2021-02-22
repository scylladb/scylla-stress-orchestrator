#!/bin/python3

import common
from common import CassandraStress
from common import Iteration
from common import DiskExplorer
from common import Ssh
from common import Fio

properties          = common.load_yaml('properties.yml')
ssh_options         =  properties['ssh_options']
user                = "fedora"
environment         = common.load_yaml('environment.yml')
iteration           = Iteration("disk-r5b.2xlarge")
public_ips          = environment['cluster_public_ips']
dir                 = "/mnt/data"
dev                 = "/dev/nvme1n1"

def make_data_dir(ip, dev, dir):
    ssh = Ssh(ip, user, ssh_options)
    ssh.run(f"sudo mkfs -t xfs {dev}")
    ssh.run(f"sudo mkdir {dir}")
    ssh.run(f"sudo mount {dev} {dir}")
    ssh.run(f"sudo chown -R {user} {dir}")
    ssh.run(f"sudo chmod -R g+rw {dir}")
    
make_data_dir(public_ips[0], dev, dir)    
    
#diskExplorer = DiskExplorer(public_ips, user, ssh_options)
#diskExplorer.install()
#diskExplorer.run(f"-o diskplorer -d {dir}")
#diskExplorer.download(iteration.dir)

fio = Fio(public_ips, user, ssh_options)
fio.install()
fio.run(f"--filename={dev} --direct=1 --rw=randread --bs=4k --ioengine=libaio --iodepth=256 --runtime=120 --numjobs=4 --time_based --group_reporting --name=iops-test-job --eta-newline=1 --readonly --output bla")
fio.download(iteration.dir)
