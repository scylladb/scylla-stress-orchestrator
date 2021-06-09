#!/bin/python3

import sys
from scyllaso import common
from scyllaso.cs import CassandraStress
from scyllaso.common import Iteration
from scyllaso.scylla import Scylla
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

TARGET_DATASET_SIZE = props['target_dataset_size_gb'] * 1024 * 1024 * 1024

REPLICATION_FACTOR = 1
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

THROTTLE = props["loading_total_throttle"] // loadgenerator_count
cs.stress_seq_range(ROW_COUNT, 'write cl=QUORUM', f'-schema "replication(strategy=SimpleStrategy,replication_factor={REPLICATION_FACTOR})" "compaction(strategy={COMPACTION_STRATEGY})" -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 maxPending=1024 -rate "threads=300 throttle={THROTTLE}/s" -node {cluster_string}')

cluster.nodetool("flush")

confirm = input("Has compaction finished? Input 'yes':")
while confirm != 'yes':
    confirm = input("Has compaction finished? Input 'yes':")

print("Run started at:", datetime.now().strftime("%H:%M:%S"))

# Background load
BACKGROUND_LOAD_OPS = props["background_total_load_ops"] // loadgenerator_count
background_load = cs.loop_stress(f'mixed ratio\\(write=1,read=1\\) duration=5m cl=QUORUM -pop dist=UNIFORM\\(1..{ROW_COUNT}\\) -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=700 fixed={BACKGROUND_LOAD_OPS}/s" -node {cluster_string}')

iteration = Iteration(f'{profile_name}/compact', ignore_git=True)

compact_start = datetime.now()

for i in range(len(cluster_public_ips)):
    print("Compacting node", i, "started at:", datetime.now().strftime("%H:%M:%S"))
    cluster.nodetool("compact", i)
    print("Compacting node", i, "ended at:", datetime.now().strftime("%H:%M:%S"))

compact_end = datetime.now()

with open(f'{iteration.dir}/result.txt', 'a') as writer:
    writer.write(f'Major compaction on all nodes took (s): {(compact_end - compact_start).total_seconds()}\n')

print("Run ended at:", datetime.now().strftime("%H:%M:%S"))

background_load.request_stop()
background_load.join()
print("Background load ended:", datetime.now().strftime("%H:%M:%S"))
