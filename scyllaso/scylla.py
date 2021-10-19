from time import sleep
from scyllaso.ssh import PSSH, SSH
from scyllaso.util import log, run_parallel, log_important, log_machine
from scyllaso.cql import wait_for_cql_start


def clear_cluster(cluster_public_ips, cluster_user, ssh_options, duration_seconds=90):
    log("Shutting down cluster and removing all data")
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options)
    # pssh.exec("nodetool flush")
    log("Stopping scylla")
    pssh.exec("sudo systemctl stop scylla-server")
    log("Removing data dir")
    pssh.exec("sudo rm -fr /var/lib/scylla/data/*")
    log("Removing commit log")
    pssh.exec("sudo rm -fr /var/lib/scylla/commitlog/*")
    log("Starting scylla")
    pssh.exec("sudo systemctl start scylla-server")
    log(f"Waiting {duration_seconds} seconds")
    sleep(duration_seconds)
    log("Cluster cleared and restarted")


def restart_cluster(cluster_public_ips, cluster_user, ssh_options, duration_seconds=90):
    log("Restart cluster ")
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options)
    log("nodetool drain")
    pssh.exec("nodetool drain")
    log("sudo systemctl restart scylla-server")
    pssh.exec("sudo systemctl restart scylla-server")
    log(f"Waiting {duration_seconds} seconds")
    sleep(duration_seconds)
    log("Cluster restarted")


def nodes_remove_data(cluster_user, ssh_options, *public_ips):
    log(f"Removing data from nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options)
    pssh.exec("sudo rm -fr /var/lib/scylla/data/*")
    pssh.exec("sudo rm -fr /var/lib/scylla/commitlog/*")
    log(f"Removing data from nodes {public_ips}: done")


def nodes_stop(cluster_user, ssh_options, *public_ips):
    log(f"Stopping nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options)
    pssh.exec("nodetool flush")
    pssh.exec("sudo systemctl stop scylla-server")
    log(f"Stopping nodes {public_ips}: done")


def nodes_start(cluster_user, ssh_options, *public_ips):
    log(f"Starting nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options)
    pssh.exec("sudo systemctl start scylla-server")
    log(f"Starting nodes {public_ips}: done")


# Assumes Scylla was started from official Scylla AMI.
class Scylla:

    def __init__(self, cluster_public_ips, cluster_private_ips, seed_private_ip, properties):
        self.properties = properties
        self.cluster_public_ips = cluster_public_ips
        self.cluster_private_ips = cluster_private_ips
        self.seed_private_ip = seed_private_ip
        self.ssh_user = properties['cluster_user']

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)

        # Scylla AMI automatically performs setup
        # and then starts up. Each node is a separate 1-node cluster.
        # Here, we wait for this startup.
        wait_for_cql_start(ip)

        # Scylla started. Now we stop it and wipe
        # the data it generated.

        # FIXME - stop scylla-server more forcefully?
        ssh.exec("sudo systemctl stop scylla-server")
        ssh.exec("sudo rm -rf /var/lib/scylla/data/*")
        ssh.exec("sudo rm -rf /var/lib/scylla/commitlog/*")

        # Patch configuration files
        ssh.exec("sudo sed -i \"s/cluster_name:.*/cluster_name: cluster1/g\" /etc/scylla/scylla.yaml")
        ssh.exec(f'sudo sed -i \"s/seeds:.*/seeds: {self.seed_private_ip} /g\" /etc/scylla/scylla.yaml')
        ssh.exec("sudo sh -c \"echo 'compaction_static_shares: 100' >> /etc/scylla/scylla.yaml\"")
        ssh.exec("sudo sh -c \"echo 'compaction_enforce_min_threshold: true' >> /etc/scylla/scylla.yaml\"")

    def install(self):
        log_important("Installing Scylla: started")
        run_parallel(self.__install, [(ip,) for ip in self.cluster_public_ips])
        log_important("Installing Scylla: done")

    def append_configuration(self, configuration):
        log(f"Appending configuration to nodes {self.cluster_public_ips}: {configuration}")
        pssh = PSSH(self.cluster_public_ips, self.ssh_user, self.properties['ssh_options'])
        pssh.exec(f"sudo sh -c \"echo '{configuration}' >> /etc/scylla/scylla.yaml\"")

    def start(self):
        log(f"Starting Scylla nodes {self.cluster_public_ips}")
        for public_ip in self.cluster_public_ips:
            ssh = self.__new_ssh(public_ip)
            ssh.exec("sudo systemctl start scylla-server")
            wait_for_cql_start(public_ip)
            log_machine(public_ip, "Node finished bootstrapping")
        log(f"Starting Scylla nodes {self.cluster_public_ips}: done")

    def nodetool(self, command, load_index=None):
        if load_index is None:
            run_parallel(self.nodetool, [(command, i) for i in range(len(self.cluster_private_ips))])
        else:
            ssh = self.__new_ssh(self.cluster_public_ips[load_index])
            ssh.exec(f"nodetool {command}")

    def stop(self, load_index=None, erase_data=False):
        if load_index is None:
            log("Not implemented!")
        else:
            self.nodetool("drain", load_index=load_index)
            ssh = self.__new_ssh(self.cluster_public_ips[load_index])
            ssh.exec("sudo systemctl stop scylla-server")

            if erase_data:
                ssh.exec("sudo rm -rf /var/lib/scylla/data/*")
                ssh.exec("sudo rm -rf /var/lib/scylla/commitlog/*")
