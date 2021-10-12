import os
import time

from scyllaso import common


def env_to_inventory():
    props = common.load_yaml('properties.yml')
    cluster_user = props['cluster_user']
    prometheus_user = props['prometheus_user']

    env = common.load_yaml('environment.yml')
    cluster_private_ips = env['cluster_private_ips']
    cluster_public_ips = env['cluster_public_ips']

    key = "/eng/scylla/scylla-ansible-roles/ansible-scylla-node/foo/key"

    inventory = "#inventory.ini\n"
    inventory = "[scylla-manager]\n"
    prometheus_public_ip = env['prometheus_public_ip']
    inventory = f"{prometheus_public_ip} ansible_connection=ssh ansible_user={prometheus_user} ansible_ssh_private_key_file={key}\n\n"

    inventory += "[scylla]\n"
    extra = f"ansible_connection=ssh ansible_user={cluster_user} ansible_ssh_private_key_file={key} dc=us-east1 rack=rack-b"

    for public_ip in cluster_public_ips:
        line = f"{public_ip} {extra}\n"
        inventory += line

    inventory_file = open('inventory.ini', 'w')
    inventory_file.write(inventory)
    inventory_file.close()
