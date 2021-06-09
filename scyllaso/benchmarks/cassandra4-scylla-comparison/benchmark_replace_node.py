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
    raise Exception("Usage: ./benchmark_replace_node.py [PROFILE_NAME]")

profile_name = sys.argv[1]

# Load properties
props = common.load_yaml(f'{profile_name}.yml')
env = common.load_yaml(f'environment_{profile_name}.yml')

start_count = len(env['cluster_private_ips']) - 1

cluster_private_ips = env['cluster_private_ips'][:start_count]
cluster_string = ",".join(cluster_private_ips[:start_count])
new_node_private_ips = env['cluster_private_ips'][start_count:]

cluster_public_ips = env['cluster_public_ips'][:start_count]
new_node_public_ips = env['cluster_public_ips'][start_count:]

all_public_ips = env['cluster_public_ips']
all_private_ips = env['cluster_private_ips']

loadgenerator_public_ips = env['loadgenerator_public_ips']
loadgenerator_count = len(loadgenerator_public_ips)

# Run parameters

# Row size of default cassandra-stress workload.
# Measured experimentally.
ROW_SIZE_BYTES = 210 * 1024 * 1024 * 1024 / 720_000_000

# 1TB per node
# TARGET_DATASET_SIZE = len(cluster_private_ips) * 1024 * 1024 * 1024 * 1024
TARGET_DATASET_SIZE = props['target_dataset_size_gb'] * 1024 * 1024 * 1024

REPLICATION_FACTOR = 3
COMPACTION_STRATEGY = props['compaction_strategy']
ROW_COUNT = int(TARGET_DATASET_SIZE / ROW_SIZE_BYTES / REPLICATION_FACTOR)

BACKGROUND_LOAD_OPS = 25000

# Start Scylla/Cassandra nodes (except one to be a replacement node later)
if props['cluster_type'] == 'scylla':
    cluster = Scylla(all_public_ips, all_private_ips, all_private_ips[0], props)
    cluster.install()
    cluster = Scylla(cluster_public_ips, cluster_private_ips, cluster_private_ips[0], props)
    cluster.start()
else:
    cluster = Cassandra(all_public_ips, all_private_ips, all_private_ips[0], props)
    cluster.install()
    if "cassandra_extra_env_opts" in props:
        cluster.append_env_configuration(props["cassandra_extra_env_opts"])
    cluster = Cassandra(cluster_public_ips, cluster_private_ips, cluster_private_ips[0], props)
    cluster.start()

print("Nodes started at:", datetime.now().strftime("%H:%M:%S"))

# Setup cassandra stress
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

# Background load
background_load = cs.loop_stress(f'mixed ratio\\(write=1,read=1\\) duration=5m cl=QUORUM -pop dist=UNIFORM\\(1..{ROW_COUNT}\\) -log hdrfile=profile.hdr -graph file=report.html title=benchmark revision=benchmark-0 -mode native cql3 -rate "threads=700 throttle={BACKGROUND_LOAD_OPS // loadgenerator_count}/s" -node {cluster_string}')

iteration = Iteration(f'{profile_name}/replace-node', ignore_git=True)

# Turn off node to be replaced.
cluster.stop(load_index=(start_count - 1), erase_data=True)

replace_node_start = datetime.now()

# Start a replacement node
if props['cluster_type'] == 'scylla':
    cluster = Scylla(new_node_public_ips, new_node_private_ips, all_private_ips[0], props)
    cluster.append_configuration(f"replace_address_first_boot: {cluster_private_ips[-1]}")
    cluster.start()
else:
    cluster = Cassandra(new_node_public_ips, new_node_private_ips, all_private_ips[0], props)
    cluster.append_env_configuration(f"JVM_OPTS=\"$JVM_OPTS -Dcassandra.replace_address={cluster_private_ips[-1]}\"")
    cluster.start()

replace_node_end = datetime.now()

print("Run ended at:", datetime.now().strftime("%H:%M:%S"))
print("Replacing node took:", (replace_node_end - replace_node_start).total_seconds(), "seconds.")

with open(f'{iteration.dir}/result.txt', 'a') as writer:
    writer.write(f'Replacing node took (s): {(replace_node_end - replace_node_start).total_seconds()}\n')

background_load.request_stop()
background_load.join()
print("Background load ended:", datetime.now().strftime("%H:%M:%S"))
