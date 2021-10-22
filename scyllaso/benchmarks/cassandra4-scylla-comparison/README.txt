

======================================
Latency/Throughput Benchmark
======================================

Scylla
```
profile=profile_3x_i3_4xlarge_scylla_latency_throughput_0w_100r
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_latency_throughput.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

Cassandra
```
profile=profile_3x_i3_4xlarge_cassandra_latency_throughput_0w_100r
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_latency_throughput.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

The above test will 100% reads. There are other `latency_throughput` profiles available.

======================================
New node benchmark
======================================

Scylla
```
profile=profile_3x_i3_4xlarge_scylla_new_node
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_new_nodes.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

Cassandra
```
profile=profile_3x_i3_4xlarge_cassandra_new_node
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_new_nodes.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

There are other new_node profiles available.

======================================
Major compaction benchmark
======================================

Scylla
```
profile=profile_1x_i3_4xlarge_scylla_compaction
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_major_compaction.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

Cassandra
```
profile=profile_1x_i3_4xlarge_cassandra_compaction
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_major_compaction.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

======================================
Repair
======================================

Scylla
```
profile=profile_3x_i3_4xlarge_scylla_repair
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_repair.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

Cassandra
```
profile=profile_3x_i3_4xlarge_cassandra_repair
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_repair.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

There are other 'repair' profiles available.

======================================
Replace node
======================================

Scylla
```
profile=profile_3x_i3_4xlarge_scylla_replace_node
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_replace_node.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

Cassandra
```
profile=profile_3x_i3_4xlarge_cassandra_replace_node
provision_terraform ec2 --workspace $profile
yes yes | ./benchmark_replace_node.py $profile
./download_prometheus.py $profile
unprovision_terraform ec2 --workspace $profile
```

There are other new_node profiles available.