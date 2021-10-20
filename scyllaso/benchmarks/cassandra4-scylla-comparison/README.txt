
Runs the `benchmark_new_nodes` with the `sanity_check_profile_3x_cassandra_new_node_lcs` profile.

```
profile=sanity_check_profile_3x_cassandra_new_node_lcs

provision_terraform ec2 --workspace $profile

yes yes | ./benchmark_new_nodes.py $profile

./download_prometheus.py $profile

unprovision_terraform ec2 --workspace $profile
```