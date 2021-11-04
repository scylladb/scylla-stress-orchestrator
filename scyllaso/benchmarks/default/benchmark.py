#!/bin/python3

from scyllaso import common
from scyllaso import scylla
from scyllaso.cs import CassandraStress
from scyllaso.common import Iteration
from scyllaso import prometheus

# Load the properties
props = common.load_yaml('properties.yml')
items = props["items"]
duration = props["duration"]
warmup_seconds = props["warmup_seconds"]
rate = props["rate"]
ops = props["ops"]
profile = props["profile"]

# Load information about the created machines.
env = common.load_yaml('environment.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

# Start with a clear prometheus.
prometheus.clear(env, props)

# Restart to cluster to make sure the Scylla starts fresh
# e.g. the memtable is flushed.
scylla.restart_cluster(env['cluster_public_ips'], props['cluster_user'], props['ssh_options'])

iteration = Iteration(props["benchmark_name"])
# Setup cassandra stress
cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()
cs.upload(profile)
cs.stress(f'user profile=./{profile} "{ops}" duration={duration} -pop seq=1..{items} -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 maxPending=1024 -rate {rate} -node {cluster_string}')
cs.collect_results(iteration.dir, warmup_seconds=warmup_seconds)

prometheus.download_and_clear(env, props, iteration)

print("Call 'unprovision_terraform.py' to destroy the created infrastructure!")
