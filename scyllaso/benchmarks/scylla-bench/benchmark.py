#!/bin/python3

from scyllaso import common
from scyllaso import scylla
from scyllaso.scylla_bench import ScyllaBench
from scyllaso.common import Iteration
from scyllaso import prometheus

props = common.load_yaml('properties.yml')
env = common.load_yaml('environment.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

prometheus.clear(env, props)

scylla.restart_cluster(env['cluster_public_ips'], props['cluster_user'], props['ssh_options'])

iteration = Iteration(props["benchmark_name"])
bench = ScyllaBench(env['loadgenerator_public_ips'], props)
bench.install()
bench.prepare()
bench.stress(f'-workload sequential -mode write -partition-count {props["items"]} -nodes {cluster_string} -duration {props["duration"]} -host-selection-policy=token-aware')
bench.collect_results(iteration.dir)

prometheus.download_and_clear(env, props, iteration)

print("Call 'unprovision_terraform.py' to destroy the created infrastructure!")

