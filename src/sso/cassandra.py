 
import os
import time

from datetime import datetime
from sso.hdr import HdrLogProcessor
from sso.ssh import SSH
from sso.util import run_parallel, find_java, WorkerThread, log_important, log_machine
from sso.network_wait import wait_for_cql_start

class Cassandra:

    def __init__(self, cluster_public_ips, cluster_private_ips, properties, cassandra_version=None):
        self.properties = properties
        self.cluster_public_ips = cluster_public_ips
        self.cluster_private_ips = cluster_private_ips
        if cassandra_version is not None:
            self.cassandra_version = cassandra_version
        else:
            self.cassandra_version = properties['cassandra_version']
            
        self.ssh_user = properties['cluster_user']
        # trigger early detection of missing java.
        find_java(properties)
  
    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)
        ssh.update()
        log_machine("Installing Cassandra: started",ip)      
        ssh.install_one('openjdk-8-jdk', 'java-1.8.0-openjdk')
        ssh.install('wget')
        seeds = ",".join(self.cluster_private_ips)
        private_ip = self.__find_private_ip(ip)
        ssh.exec(f"""
            set -e
            
            if [ -d 'apache-cassandra-{self.cassandra_version}' ]; then
                echo Cassandra {self.cassandra_version} already installed.
                exit 0
            fi
            
            wget -q -N https://mirrors.netix.net/apache/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz
            tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz
            cd apache-cassandra-{self.cassandra_version}
            sudo sed -i \"s/seeds:.*/seeds: {seeds} /g\" conf/cassandra.yaml
            sudo sed -i \"s/listen_address:.*/listen_address: {private_ip} /g\" conf/cassandra.yaml
            sudo sed -i \"s/rpc_address:.*/rpc_address: {private_ip} /g\" conf/cassandra.yaml
        """)
        log_machine("Installing Cassandra: done",ip)      

    def __find_private_ip(self, public_ip):
        index = self.cluster_public_ips.index(public_ip)
        return self.cluster_private_ips[index]

    def install(self):
        log_important("Installing Cassandra: started")
        run_parallel(self.__install, [(ip,) for ip in self.cluster_public_ips])
        log_important("Installing Cassandra: done")
        
    def __start(self, ip):
        log_machine("Starting Cassandra: started",ip)
        ssh = self.__new_ssh(ip)
        ssh.exec(f"""
            set -e
            cd apache-cassandra-{self.cassandra_version}
            if [ -f 'cassandra.pid' ]; then
                pid=$(cat cassandra.pid)
                kill $pid
                rm 'cassandra.pid'
            fi
            bin/cassandra -p cassandra.pid 2>&1 >> cassandra.out & 
            """)

        log_machine("Starting Cassandra: done",ip)      

    def start(self):
        log_important("Start Cassandra: started")
        for ip in self.cluster_public_ips:
            self.__start(ip)
            wait_for_cql_start(ip)
        log_important("Start Cassandra: done")
        
    def __stop(self, ip):
        print_indent_machine("Stopping Cassandra: started",ip)
        ssh = self.__new_ssh(ip)
        ssh.exec(f"""
            set -e
            cd apache-cassandra-{self.cassandra_version}
            if [ -f 'cassandra.pid' ]; then
                pid=$(cat cassandra.pid)
                kill $pid
                rm 'cassandra.pid'
            fi
            """)
        
        print(f'    [{ip}] Stopping Cassandra: done')

    def stop(self):
        log_important("Stop Cassandra: started")
        run_parallel(self.__stop, [(ip,) for ip in self.cluster_public_ips])
        log_important("Stop Cassandra: done")    
