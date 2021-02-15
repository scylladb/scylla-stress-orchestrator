#!/bin/python3

import common
from common import CassandraStress
from common import Iteration
from common import DiskExplorer

properties = common.load_yaml('properties.yml')
environment = common.load_yaml('environment.yml')

iteration = Iteration("foobar")

diskExplorer = DiskExplorer(environment['cluster_public_ips'], properties['load_generator_user'], properties['ssh_options')
diskExplorer.install()
diskExplorer.run("-o diskplorer -d /data")
diskExplorer.download(iteration.dir)
