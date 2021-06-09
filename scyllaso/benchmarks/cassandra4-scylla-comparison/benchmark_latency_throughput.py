#!/bin/python3

import sys
import os
import time

from scyllaso import common
from scyllaso.cs import CassandraStress
from scyllaso.common import Iteration
from scyllaso.scylla import Scylla
from scyllaso.hdr import parse_profile_summary_file
from scyllaso.cassandra import Cassandra
from datetime import datetime

print("Test started at:", datetime.now().strftime("%H:%M:%S"))

if len(sys.argv) < 2:
    raise Exception("Usage: ./benchmark_latency_throughput.py [PROFILE_NAME]")

# Load properties
profile_name = sys.argv[1]
props = common.load_yaml(f'{profile_name}.yml')
env = common.load_yaml(f'environment_{profile_name}.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)
cluster_public_ips = env['cluster_public_ips']
loadgenerator_public_ips = env['loadgenerator_public_ips']
loadgenerator_count = len(loadgenerator_public_ips)

# Run parameters

# Row size of default cassandra-stress workload.
# Measured experimentally.
ROW_SIZE_BYTES = 210 * 1024 * 1024 * 1024 / 720_000_000

# 1TB per node
#TARGET_DATASET_SIZE = len(cluster_private_ips) * 1024 * 1024 * 1024 * 1024
TARGET_DATASET_SIZE = props['target_dataset_size_gb'] * 1024 * 1024 * 1024

REPLICATION_FACTOR = 3
COMPACTION_STRATEGY = props['compaction_strategy']
ROW_COUNT = int(TARGET_DATASET_SIZE / ROW_SIZE_BYTES / REPLICATION_FACTOR)

START_RATE     = props['start_rate'] #10000
RATE_INCREMENT = props['rate_increment'] #10000
DURATION_MINUTES = props['duration_minutes']

MAX_90_PERCENTILE_LATENCY = 1000.0

WRITE_COUNT = props['write_count']
READ_COUNT = props['read_count']

# Start Scylla/Cassandra nodes
if props['cluster_type'] == 'scylla':
    cluster = Scylla(env['cluster_public_ips'], env['cluster_private_ips'], env['cluster_private_ips'][0], props)
    cluster.install()
    cluster.start()
else:
    cluster = Cassandra(env['cluster_public_ips'], env['cluster_private_ips'], env['cluster_private_ips'][0], props)
    cluster.install()
    if "cassandra_extra_env_opts" in props:
        cluster.append_env_configuration(props["cassandra_extra_env_opts"])
    cluster.start()

print("Nodes started at:", datetime.now().strftime("%H:%M:%S"))

cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()

print("Loading started at:", datetime.now().strftime("%H:%M:%S"))

THROTTLE = (100000 // loadgenerator_count) if props['cluster_type'] == 'scylla' else (56000 // loadgenerator_count)

cs.stress_seq_range(ROW_COUNT, 'write cl=QUORUM', f'-schema "replication(strategy=SimpleStrategy,replication_factor={REPLICATION_FACTOR})" "compaction(strategy={COMPACTION_STRATEGY})" -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=700 throttle={THROTTLE}/s" -node {cluster_string}')

cluster.nodetool("flush")

confirm = input("Has compaction finished? Input 'yes':")
while confirm != 'yes':
    confirm = input("Has compaction finished? Input 'yes':")    

print("Run started at:", datetime.now().strftime("%H:%M:%S"))

rate = START_RATE

while True:
    print("Run iteration started at:", datetime.now().strftime("%H:%M:%S"))

    iteration = Iteration(f'{profile_name}/cassandra-stress-{rate}', ignore_git=True)

    cs.stress(f'mixed ratio\\(write={WRITE_COUNT},read={READ_COUNT}\\) duration={DURATION_MINUTES}m cl=QUORUM -pop dist=UNIFORM\\(1..{ROW_COUNT}\\) -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=500 fixed={rate // loadgenerator_count}/s" -node {cluster_string}')

    cs.collect_results(iteration.dir)

    if WRITE_COUNT > 0:
        write_profile_summary = parse_profile_summary_file(f'{iteration.dir}/profile-summary.txt', 'WRITE')
        print('WRITE_PROFILE', write_profile_summary)

    if READ_COUNT > 0:
        read_profile_summary = parse_profile_summary_file(f'{iteration.dir}/profile-summary.txt', 'READ')
        print('READ_PROFILE', read_profile_summary)

    with open(f'{iteration.dir}/parsed_profile_summary_file.txt', 'a') as writer:
        if WRITE_COUNT > 0:
            writer.write(f'WRITE_PROFILE: {write_profile_summary}\n')
        if READ_COUNT > 0:
            writer.write(f'READ_PROFILE: {read_profile_summary}\n')

    if WRITE_COUNT > 0 and write_profile_summary.p90_latency_ms > MAX_90_PERCENTILE_LATENCY:
        break
    if READ_COUNT > 0 and read_profile_summary.p90_latency_ms > MAX_90_PERCENTILE_LATENCY:
        break

    rate += RATE_INCREMENT

print("Run ended at:", datetime.now().strftime("%H:%M:%S"))
