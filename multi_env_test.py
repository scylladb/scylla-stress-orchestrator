#!/bin/python3

import common
from common import CassandraStress
from common import Iteration
import terraform

properties = common.load_yaml('properties.yml')
 
instance_types = ["c5.xlarge", "c5.2xlarge", "c5.4xlarge"]
terraform_plan = properties.get('terraform_plan')
for instance_type in instance_types:
    print("--------------------------------------------------")
    print(instance_type)
    print("--------------------------------------------------")

    terraform.apply(terraform_plan,f'-var="cluster_instance_type={instance_type}"')
    environment = common.load_yaml('environment.yml')
 
    cluster_private_ips = environment['cluster_private_ips']
    cluster_string = ",".join(cluster_private_ips)

    iteration = Iteration(instance_type)
    
    cs = CassandraStress(environment['loadgenerator_public_ips'], properties)
    cs.install()
    cs.prepare();
    cs.stress(f'write n=2m -log hdrfile=store.hdr -graph file=store.html title=store revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')   
    cs.get_results(iteration.dir)

    terraform.destroy(terraform_plan)
