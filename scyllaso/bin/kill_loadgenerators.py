from scyllaso import common
from scyllaso.ssh import PSSH


def cli():
    props = common.load_yaml('properties.yml')
    env = common.load_yaml('environment.yml')
    pssh = PSSH(env['loadgenerator_public_ips'], props['load_generator_user'], props['ssh_options'])
    pssh.exec(f'killall -q -9 java')
    pssh.exec(f'killall -q -9 go/bin/scylla-bench')
