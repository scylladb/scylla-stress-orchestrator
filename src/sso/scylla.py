import os
import shlex
from time import sleep
from sso.ssh import PSSH
from ssh.util import log

def clear_cluster(cluster_public_ips, cluster_user, ssh_options, duration_seconds=90):
    log("Shutting down cluster and removing all data")
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options);
    #pssh.exec("nodetool flush")
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
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options);
    log("nodetool drain")
    pssh.exec("nodetool drain")
    log("sudo systemctl stop scylla-server")
    pssh.exec("sudo systemctl stop scylla-server")
    log("sudo systemctl start scylla-server")
    pssh.exec("sudo systemctl start scylla-server")
    log(f"Waiting {duration_seconds} seconds")
    sleep(duration_seconds)
    log("Cluster restarted")


def nodes_remove_data(cluster_user, ssh_options, *public_ips):
    log(f"Removing data from nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("sudo rm -fr /var/lib/scylla/data/*")
    pssh.exec("sudo rm -fr /var/lib/scylla/commitlog/*")
    log(f"Removing data from nodes {public_ips}: done")


def nodes_stop(cluster_user, ssh_options, *public_ips):
    log(f"Stopping nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("nodetool flush")
    pssh.exec("sudo systemctl stop scylla-server")
    log(f"Stopping nodes {public_ips}: done")


def nodes_start(cluster_user, ssh_options, *public_ips):
    log(f"Starting nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("sudo systemctl start scylla-server")
    log(f"Starting nodes {public_ips}: done")
