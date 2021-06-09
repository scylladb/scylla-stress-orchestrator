#!/bin/python3

import sys
from scyllaso import common
from scyllaso.cs import CassandraStress
from scyllaso.scylla import Scylla
from datetime import datetime

print("Test started at:", datetime.now().strftime("%H:%M:%S"))

if len(sys.argv) < 2:
    raise Exception("Usage: ./benchmark_drivers.py [PROFILE_NAME]")

# Load properties
profile_name = sys.argv[1]
props = common.load_yaml(f'{profile_name}.yml')
env = common.load_yaml(f'environment_{profile_name}.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)
cluster_public_ips = env['cluster_public_ips']
loadgenerator_public_ips = env['loadgenerator_public_ips']
loadgenerator_count = len(loadgenerator_public_ips)

ROW_SIZE_BYTES = 300

# 20GB per node
TARGET_DATASET_SIZE = len(cluster_private_ips) * 20 * 1024 * 1024 * 1024

REPLICATION_FACTOR = 3
ROW_COUNT = int(TARGET_DATASET_SIZE / ROW_SIZE_BYTES / REPLICATION_FACTOR)

# Start Scylla nodes
s = Scylla(env['cluster_public_ips'], env['cluster_private_ips'], env['cluster_private_ips'][0], props)
s.install()
s.start()

print("Nodes started at:", datetime.now().strftime("%H:%M:%S"))

cs = CassandraStress(env['loadgenerator_public_ips'], props, scylla_tools=False)
cs.install()
cs.prepare()

print("Loading started at:", datetime.now().strftime("%H:%M:%S"))

cs.stress_seq_range(ROW_COUNT, 'write cl=QUORUM', f'-schema "replication(strategy=SimpleStrategy,replication_factor={REPLICATION_FACTOR})" -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=300 throttle=50000/s" -node {cluster_string}')

print("Loading ended at:", datetime.now().strftime("%H:%M:%S"))