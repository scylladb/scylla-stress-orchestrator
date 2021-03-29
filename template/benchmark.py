#!/bin/python3

import sys
import os

sys.path.insert(1, f"{os.environ['SSO']}/src/")

from time import sleep
from sso import common
from sso.cs import CassandraStress
from sso.common import Iteration
from sso.ssh import PSSH


props = common.load_yaml('properties.yml')
env = common.load_yaml('environment.yml')
 
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

iteration = Iteration("dummy-benchmark")

cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()

cs.upload("stress_example.yaml")

# insert data
cs.stress(f'user profile=./stress_example.yaml "ops(insert=1)" n=1m -mode native cql3 -rate threads=50 -node {cluster_string}')  

# actual work
cs.stress(f'user profile=./stress_example.yaml "ops(singleclothes=1, insert=1)" n=10m -log hdrfile=profile.hdr -graph file=profile.html title=store revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')  

cs.collect_results(iteration.dir)
