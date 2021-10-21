#!/bin/python3

from scyllaso import common
from scyllaso import scylla
from scyllaso.cs import CassandraStress
from scyllaso.common import Iteration
from scyllaso import prometheus

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
duration = "12m"
# 2 minutes of warmup are removed from the duration.
warmup_seconds = 120

# Configuration for throughput test 
rate = f'threads=200'
# Configuration for a latency: fixed number of requests per second
# rate = f'threads=200 fixed="2000/s"'

profile = "stress_profile.yaml"

cs.upload(profile)

# Insert the test data.
cs.insert(profile, items, cluster_string)

# Restart to cluster to make sure the Scylla starts fresh 
# e.g. the memtable is flushed.
scylla.restart_cluster(env['cluster_public_ips'], props['cluster_user'], props['ssh_options'])

# Actual benchmark
cs.stress(f'user profile=./{profile} "ops(insert=1)" duration={duration} -pop seq=1..{items} -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate {rate} -node {cluster_string}')

# collect the results.
cs.collect_results(iteration.dir, warmup_seconds=warmup_seconds)

# Download and clear the prometheus data (can take a lot of time/space)
prometheus.download_and_clear(env, props, iteration)

# Automatically terminates the cluster.
#terraform.destroy(props['terraform_plan'])
print("Call 'unprovision_terraform.py' to destroy the created infrastructure!")
