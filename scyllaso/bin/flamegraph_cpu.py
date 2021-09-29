import sys
import os
import argparse
from scyllaso import common
from scyllaso.perf import Perf


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("CPU", help="The CPU to profile", nargs="?")
    parser.add_argument("-o", "--output", help="The name (no extension) of the output file", default="flamegraph")
    parser.add_argument("-a", "--args", help="The extra perf record arguments", default="--call-graph lbr -F99")
    parser.add_argument("-d", "--duration", help="Duration to profile in seconds (default 30) ", type=int, default=30)
    parser.add_argument("-l", "--list", help="Runs `perf list -v`", action='store_true')
    args = parser.parse_args()

    props = common.load_yaml('properties.yml')
    env = common.load_yaml('environment.yml')
    cluster_public_ips = env['cluster_public_ips']

    perf = Perf(cluster_public_ips, props['cluster_user'], props['ssh_options'])
    perf.install()

    if args.list:
        perf.list()
    else:
        cpu = args.CPU
        if not cpu:
            print("No CPU was selected")
            sys.exit(1)

        print(f"Profiling CPU {cpu}")
        perf.flamegraph_cpu(cpu, os.getcwd(), duration_seconds=args.duration, args=args.args, output=args.output)
