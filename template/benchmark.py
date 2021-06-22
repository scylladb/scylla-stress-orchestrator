#!/bin/python3

import sys
import os

sys.path.insert(1, f"{os.environ['SSO']}/src/")

from time import sleep
from sso import common
from sso import terraform
from sso.cs import CassandraStress
from sso.common import Iteration
from sso import prometheus

# Load the properties
props = common.load_yaml('properties.yml')

# Provision the machines.
# terraform.apply(props['terraform_plan'])

# Load information about the created machines.
env = common.load_yaml('environment.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

iteration = Iteration("dummy-benchmark")

# Setup cassandra stress
cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()

# Total number of items.
items = 10_000_000

# The running time of the benchmark
duration = "2m"

# The number of threads executing requests on each load generator
threads = 200

cs.upload("stress_example.yaml")

# Insert the test data.
cs.insert("stress_example.yaml", items, cluster_string)
 
# Actual benchmark
cs.stress(f'user profile=./stress_example.yaml "ops(insert=1)" duration={duration} -pop seq=1..{items} -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate threads={threads} -node {cluster_string}')  

# collect the results.
cs.collect_results(iteration.dir)

# Download and clear the prometheus data (can take a lot of time/space)
prometheus.download_and_clear(env, props, iteration)

# Automatically terminates the cluster.
#terraform.destroy(props['terraform_plan'])
print("Call 'unprovision-terraform' to destroy the created infrastructure!")
