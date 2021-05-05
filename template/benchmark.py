#!/bin/python3

import sys
import os

sys.path.insert(1, f"{os.environ['SSO']}/src/")

from time import sleep
from sso import common
from sso import terraform
from sso.cs import CassandraStress
from sso.common import Iteration

# Load the properties
props = common.load_yaml('properties.yml')

# Provision the machines.
terraform.apply(props['terraform_plan'])

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

cs.upload("stress_example.yaml")

# Insert the test data.
cs.insert("stress_example.yaml", items, cluster_string)
 
# Actual work
cs.stress(f'user profile=./stress_example.yaml "ops(insert=1)" duration=2m -pop seq=1..{items} -mode native cql3 -rate threads=200 -node {cluster_string}')  

# collect the results.
cs.collect_results(iteration.dir)

# Automatically terminates the cluster.
#terraform.destroy(props['terraform_plan'])
print("Call 'unprovision-terraform' to destroy the created infrastructure!")
