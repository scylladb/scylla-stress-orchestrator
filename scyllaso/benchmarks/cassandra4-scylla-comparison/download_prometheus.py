#!/bin/python3

import sys
from scyllaso import common
from scyllaso.common import Iteration
from datetime import datetime
from scyllaso import prometheus

print("Test started at:", datetime.now().strftime("%H:%M:%S"))

if len(sys.argv) < 2:
    raise Exception("Usage: ./download_prometheus.py [PROFILE_NAME]")

profile_name = sys.argv[1]

# Load properties
props = common.load_yaml(f'{profile_name}.yml')
env = common.load_yaml(f'environment_{profile_name}.yml')

iteration = Iteration(f'{profile_name}/prometheus-dump', ignore_git=True)

prometheus.download(env, props, iteration)
