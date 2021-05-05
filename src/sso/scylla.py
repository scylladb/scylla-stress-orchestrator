import os
from time import sleep
from sso.ssh import PSSH


def clear_cluster(cluster_public_ips, cluster_user, ssh_options, duration_seconds=90):
    print("Shutting down cluster and removing all data")
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options);
    #pssh.exec("nodetool flush")
    print("Stopping scylla")
    pssh.exec("sudo systemctl stop scylla-server")
    print("Removing data dir")
    pssh.exec("sudo rm -fr /var/lib/scylla/data/*")
    print("Removing commit log")
    pssh.exec("sudo rm -fr /var/lib/scylla/commitlog/*")
    print("Starting scylla")
    pssh.exec("sudo systemctl start scylla-server")
    print(f"Waiting {duration_seconds} seconds")
    sleep(duration_seconds)
    print("Cluster cleared and restarted")

    
def restart_cluster(cluster_public_ips, cluster_user, ssh_options, duration_seconds=90):
    print("Restart cluster ")
    pssh = PSSH(cluster_public_ips, cluster_user, ssh_options);
    print("nodetool drain")
    pssh.exec("nodetool drain")
    print("sudo systemctl stop scylla-server")    
    pssh.exec("sudo systemctl stop scylla-server")
    print("sudo systemctl start scylla-server")    
    pssh.exec("sudo systemctl start scylla-server")
    print(f"Waiting {duration_seconds} seconds")
    sleep(duration_seconds)
    print("Cluster restarted")


def nodes_remove_data(cluster_user, ssh_options, *public_ips):
    print(f"Removing data from nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("sudo rm -fr /var/lib/scylla/data/*")
    pssh.exec("sudo rm -fr /var/lib/scylla/commitlog/*")
    print(f"Removing data from nodes {public_ips}: done")


def nodes_stop(cluster_user, ssh_options, *public_ips):
    print(f"Stopping nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("nodetool flush")
    pssh.exec("sudo systemctl stop scylla-server")
    print(f"Stopping nodes {public_ips}: done")


def nodes_start(cluster_user, ssh_options, *public_ips):
    print(f"Starting nodes {public_ips}")
    pssh = PSSH(public_ips, cluster_user, ssh_options);
    pssh.exec("sudo systemctl start scylla-server")
    print(f"Starting nodes {public_ips}: done")
