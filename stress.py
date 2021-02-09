#!/bin/python3

import common
from common import CassandraStress
from common import Iteration

properties = common.load_yaml('properties.yml')
environment = common.load_yaml('environment.yml')
 
cluster_private_ips = environment['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

iteration = Iteration("foobar")
    
cs = CassandraStress(environment['loadgenerator_public_ips'], properties)
cs.install()
cs.prepare();
cs.stress(f'write n=20m -log hdrfile=store.hdr -graph file=store.html title=store revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')   
cs.stress(f'read  n=20m -log hdrfile=load.hdr -graph file=load.html   title=load revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')
cs.stress(f'mixed ratio\(write=1,read=3\) n=20m -log hdrfile=mixed.hdr -graph file=mixed.html title=mixed revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')   

cs.get_results(iteration.dir)


