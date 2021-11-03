#!/bin/python3

from scyllaso import common
from scyllaso.cs import CassandraStress
from scyllaso import scylla

props = common.load_yaml('properties.yml')
items = props["items"]
profile = props["profile"]

env = common.load_yaml('environment.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

scylla.clear_cluster(env['cluster_public_ips'], props['cluster_user'], props['ssh_options'])

cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()
cs.upload(profile)
cs.insert(profile, items, cluster_string)
