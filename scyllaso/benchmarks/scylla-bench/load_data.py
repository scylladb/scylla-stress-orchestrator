#!/bin/python3

from scyllaso import common
from scyllaso import scylla
from scyllaso.scylla_bench import ScyllaBench
from scyllaso.scylla import Scylla

props = common.load_yaml('properties.yml')
env = common.load_yaml('environment.yml')
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

cluster = Scylla(env['cluster_public_ips'], env['cluster_private_ips'], env['cluster_private_ips'][0], props)
cluster.install()
cluster.start()

bench = ScyllaBench(env['loadgenerator_public_ips'], props)
bench.install()
bench.prepare()
bench.insert(props["items"], cluster_string)

