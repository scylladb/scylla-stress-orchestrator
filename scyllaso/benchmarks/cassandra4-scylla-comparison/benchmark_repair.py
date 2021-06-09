#!/bin/python3

import sys
import time
from scyllaso import common
from scyllaso.cs import CassandraStress
from scyllaso.common import Iteration
from scyllaso.scylla import Scylla
from scyllaso.cassandra import Cassandra
from datetime import datetime

print("Test started at:", datetime.now().strftime("%H:%M:%S"))

if len(sys.argv) < 2:
    raise Exception("Usage: ./benchmark_repair.py [PROFILE_NAME]")

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
TARGET_DATASET_SIZE = props['target_dataset_size_gb'] * 1024 * 1024 * 1024

REPLICATION_FACTOR = 3
COMPACTION_STRATEGY = props['compaction_strategy']
ROW_COUNT = int(TARGET_DATASET_SIZE / ROW_SIZE_BYTES / REPLICATION_FACTOR)

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

cs.stress_seq_range(ROW_COUNT, 'write cl=QUORUM',
                    f'-schema "replication(strategy=SimpleStrategy,replication_factor={REPLICATION_FACTOR})" "compaction(strategy={COMPACTION_STRATEGY})" -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=700 throttle=33000/s" -node {cluster_string}')

print("Sleeping 2h")
time.sleep(60 * 60 * 2)

print("Run started at:", datetime.now().strftime("%H:%M:%S"))

iteration = Iteration(f'{profile_name}/repair_no_errors', ignore_git=True)

repair_start = datetime.now()

print("Reparing node 0 started at:", datetime.now().strftime("%H:%M:%S"))
cluster.nodetool("repair -full", 0)
print("Reparing node 0 ended at:", datetime.now().strftime("%H:%M:%S"))

repair_end = datetime.now()

with open(f'{iteration.dir}/result.txt', 'a') as writer:
    writer.write(f'Reparing node 0 took (s): {(repair_end - repair_start).total_seconds()}\n')

print("Run ended at:", datetime.now().strftime("%H:%M:%S"))
