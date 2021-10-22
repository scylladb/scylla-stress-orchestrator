from datetime import datetime
from scyllaso.ssh import PSSH, SSH
from scyllaso.util import run_parallel, find_java, log, log_important, log_machine
from scyllaso.network_wait import wait_for_cql_start
from scyllaso.raid import RAID


class Cassandra:

    def __init__(self,
                 cluster_public_ips,
                 cluster_private_ips,
                 seed_private_ip,
                 properties,
                 setup_raid=True,
                 cassandra_version=None):
        self.properties = properties
        self.cluster_public_ips = cluster_public_ips
        self.cluster_private_ips = cluster_private_ips
        self.seed_private_ip = seed_private_ip
        if cassandra_version is not None:
            self.cassandra_version = cassandra_version
        else:
            self.cassandra_version = properties['cassandra_version']

        self.ssh_user = properties['cluster_user']
        self.setup_raid = setup_raid
        # trigger early detection of missing java.
        find_java(properties)

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)
        ssh.update()
        log_machine(ip, "Installing Cassandra: started")
        ssh.install_one('openjdk-16-jdk', 'java-16-openjdk')
        ssh.install('wget')
        private_ip = self.__find_private_ip(ip)
        path_prefix = 'cassandra-raid/' if self.setup_raid else './'
        ssh.exec(f"""
            set -e
            
            if [ -d '{path_prefix}apache-cassandra-{self.cassandra_version}' ]; then
                echo Cassandra {self.cassandra_version} already installed.
                exit 0
            fi
            
            wget -q -N https://archive.apache.org/dist/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz
            tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz -C {path_prefix}
            
            wget -q https://github.com/criteo/cassandra_exporter/releases/download/2.3.5/cassandra_exporter-2.3.5.jar
        """)
        ssh.scp_to_remote("jvm11-server.options",
                          f"{path_prefix}apache-cassandra-{self.cassandra_version}/conf/jvm11-server.options")
        ssh.scp_to_remote("cassandra.yaml",
                          f"{path_prefix}apache-cassandra-{self.cassandra_version}/conf/cassandra.yaml")
        ssh.scp_to_remote("cassandra-exporter.yml", f"config.yml")
        # FIXME - heap in MB * 2
        ssh.exec("""
            sudo sh -c "echo 262144 > /proc/sys/vm/max_map_count"
        """)
        ssh.exec(f"""
            cd {path_prefix}apache-cassandra-{self.cassandra_version}
            sudo sed -i \"s/seeds:.*/seeds: {self.seed_private_ip} /g\" conf/cassandra.yaml
            sudo sed -i \"s/listen_address:.*/listen_address: {private_ip} /g\" conf/cassandra.yaml
            sudo sed -i \"s/rpc_address:.*/rpc_address: {private_ip} /g\" conf/cassandra.yaml
        """)
        log_machine(ip, "Installing Cassandra: done")

    def __find_private_ip(self, public_ip):
        index = self.cluster_public_ips.index(public_ip)
        return self.cluster_private_ips[index]

    def nodetool(self, command, load_index=None):
        if load_index is None:
            run_parallel(self.nodetool, [(command, i) for i in range(len(self.cluster_private_ips))])
        else:
            path_prefix = 'cassandra-raid/' if self.setup_raid else './'
            ssh = self.__new_ssh(self.cluster_public_ips[load_index])
            ssh.exec(f"{path_prefix}apache-cassandra-{self.cassandra_version}/bin/nodetool {command}")

    def install(self):
        log_important("Installing Cassandra: started")
        if self.setup_raid:
            log_important("Installing Cassandra: setting up RAID")
            raid = RAID(self.cluster_public_ips, self.ssh_user, '/dev/nvme*n1', 'cassandra-raid', 0, self.properties)
            raid.install()
            log_important("Installing Cassandra: finished setting up RAID")
        run_parallel(self.__install, [(ip,) for ip in self.cluster_public_ips])
        log_important("Installing Cassandra: done")

    def __start(self, ip):
        log_machine(ip, "Starting Cassandra: started")
        ssh = self.__new_ssh(ip)
        path_prefix = 'cassandra-raid/' if self.setup_raid else './'
        ssh.exec(f"""
            set -e
            cd {path_prefix}apache-cassandra-{self.cassandra_version}
            if [ -f 'cassandra.pid' ]; then
                pid=$(cat cassandra.pid)
                kill $pid || true
                while kill -0 $pid; do 
                    sleep 1
                done
                rm -f 'cassandra.pid'
            fi
            bin/cassandra -p cassandra.pid 2>&1 >> cassandra.out &
            """)
        log_machine(ip, "Starting Cassandra: done")

    def __start_exporter(self, ip):
        log_machine(ip, 'Starting exporter')
        ssh = self.__new_ssh(ip)
        ssh.exec(f"""
            java -Dorg.slf4j.simpleLogger.defaultLogLevel=trace -jar ~/cassandra_exporter-2.3.5.jar ~/config.yml >> ~/cassandra_exporter.out 2>&1 &
            """)
        log_machine(ip, 'Starting exporter: done')

    def append_env_configuration(self, configuration):
        log(f"Appending cassandra-env.sh configuration to nodes {self.cluster_public_ips}: {configuration}")
        pssh = PSSH(self.cluster_public_ips, self.ssh_user, self.properties['ssh_options'])
        path_prefix = 'cassandra-raid/' if self.setup_raid else './'
        log("configuration["+configuration+"]")
        pssh.exec(
            f'''echo '{configuration}' >> {path_prefix}apache-cassandra-{self.cassandra_version}/conf/cassandra-env.sh''')
        log(f"echo '{configuration}' >> {path_prefix}apache-cassandra-{self.cassandra_version}/conf/cassandra-env.sh")

    def start(self):
        log_important(f"Starting Cassandra nodes {self.cluster_public_ips}")
        for public_ip in self.cluster_public_ips:
            self.__start(public_ip)
            wait_for_cql_start(public_ip)
            log_machine(public_ip, f"""Node finished bootstrapping""")
            self.__start_exporter(public_ip)
        log_important(f"Starting Cassandra nodes {self.cluster_public_ips}: done")

    def __stop(self, ip):
        log_machine(ip, "Stopping Cassandra: started")
        ssh = self.__new_ssh(ip)
        path_prefix = 'cassandra-raid/' if self.setup_raid else './'
        ssh.exec(f"""
            set -e
            cd {path_prefix}apache-cassandra-{self.cassandra_version}
            if [ -f 'cassandra.pid' ]; then
                pid=$(cat cassandra.pid)
                kill $pid || true
                while kill -0 $pid; do 
                    sleep 1
                done
                rm -f 'cassandra.pid'
            fi
            """)

        log_machine(ip, 'Stopping Cassandra: done')

    def stop(self, load_index=None, erase_data=False):
        if load_index is None:
            log_important("Stop Cassandra: started")
            run_parallel(self.__stop, [(ip,) for ip in self.cluster_public_ips])
            log_important("Stop Cassandra: done")
        else:
            self.__stop(self.cluster_public_ips[load_index])

            if erase_data:
                ssh = self.__new_ssh(self.cluster_public_ips[load_index])
                path_prefix = 'cassandra-raid/' if self.setup_raid else './'
                ssh.exec(f"rm -rf {path_prefix}apache-cassandra-{self.cassandra_version}/data")
