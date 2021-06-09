#!/bin/python3

import sys
import os

sys.path.insert(1, f"{os.environ['SSO']}/src/")

from sso import common
from sso.cs import CassandraStress
from sso.common import Iteration
from sso.scylla import Scylla
from sso.hdr import parse_profile_summary_file
from sso.cassandra import Cassandra
from datetime import datetime
from sso import prometheus

print("Test started at:", datetime.now().strftime("%H:%M:%S"))

if len(sys.argv) < 2:
    raise Exception("Usage: ./download_prometheus.py [PROFILE_NAME]")

profile_name = sys.argv[1]

# Load properties
props = common.load_yaml(f'{profile_name}.yml')
env = common.load_yaml(f'environment_{profile_name}.yml')

iteration = Iteration(f'{profile_name}/prometheus-dump', ignore_git=True)

prometheus.download(env, props, iteration)
