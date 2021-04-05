import os
import time

from sso.hdr import HdrLogProcessor
from sso.ssh import SSH
from sso.util import run_parallel, WorkerThread


class CassandraStress:

    def __init__(self, load_ips, properties, scylla_tools=True):
        self.properties = properties
        self.load_ips = load_ips
        self.cassandra_version = properties['cassandra_version']
        self.ssh_user = properties['load_generator_user']
        self.scylla_tools = scylla_tools

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)
        ssh.update()
        if self.scylla_tools:
            print(f'    [{ip}] Installing cassandra-stress (Scylla): started')
            ssh.exec(f"""
                set -e
                if hash apt-get 2>/dev/null; then
                    sudo apt-get install -y apt-transport-https
                    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 5e08fbd8b5d6ec9c
                    sudo curl -L --output /etc/apt/sources.list.d/scylla.list http://downloads.scylladb.com/deb/ubuntu/scylla-4.3-$(lsb_release -s -c).list
                    sudo apt-get update -y
                    sudo apt-get install -y scylla-tools
                elif hash yum 2>/dev/null; then
                    sudo yum install  -y -q https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
                    sudo curl -o /etc/yum.repos.d/scylla.repo -L http://repositories.scylladb.com/scylla/repo/603fc559-4518-4f8e-8ceb-2851dec4ab23/centos/scylladb-4.3.repo
                    sudo yum install -y -q scylla-tools
                else
                    echo "Cannot install scylla-tools: yum/apt not found"
                    exit 1
                fi
                """)
        else:
            print(f'    [{ip}] Installing cassandra-stress (Cassandra): started')
            ssh.install_one('openjdk-8-jdk', 'java-1.8.0-openjdk')
            ssh.install('wget')
            ssh.exec(f"""
                set -e
                wget -q -N https://mirrors.netix.net/apache/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz
                tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz
            """)

        print(f'    [{ip}] Installing cassandra-stress: done')

    def install(self):
        print("============== Installing Cassandra-Stress: started =================")
        run_parallel(self.__install, [(ip,) for ip in self.load_ips])
        print("============== Installing Cassandra-Stress: done =================")

    def __stress(self, ip, cmd):
        if self.scylla_tools:
            full_cmd = f'cassandra-stress {cmd}'
        else:
            cassandra_stress_dir = f'apache-cassandra-{self.cassandra_version}/tools/bin'
            full_cmd = f'{cassandra_stress_dir}/cassandra-stress {cmd}'
        print(full_cmd)
        print(f"{ip} {full_cmd} started-------------------------------------------------------------------------")
        self.__new_ssh(ip).exec(full_cmd)
        print(f"{ip} {full_cmd} finshed-------------------------------------------------------------------------")

    def stress(self, command, load_index=None):
        if load_index is None:
            print("============== Cassandra-Stress: started ===========================")
            run_parallel(self.__stress, [(ip, command) for ip in self.load_ips])
            print("============== Cassandra-Stress: done ==============================")
        else:
            print("using load_index " + str(load_index))
            self.__stress(self.load_ips[load_index], command)

    def async_stress(self, command, load_index=None):
        thread = WorkerThread(self.stress, (command, load_index))
        thread.start()
        return thread.future

    def insert(self, profile, item_count, nodes, mode="native cql3", rate="threads=700", sequence_start=None):
        print(f"============== Inserting {item_count} items ===========================")
        start_seconds = time.time()

        per_load_generator = item_count // len(self.load_ips)
        start = sequence_start
        if sequence_start is None:
            start = 1

        end = start + per_load_generator - 1
        cmd_list = []
        for i in range(0, len(self.load_ips)):
            cmd = f'user profile={profile} "ops(insert=1)" n={per_load_generator} no-warmup -pop seq={start}..{end} -mode {mode} -rate {rate}  -node {nodes}'
            print(self.load_ips[i] + " " + cmd)
            cmd_list.append(cmd)
            start = end + 1
            end = end + per_load_generator

        futures = []
        for i in range(0, len(self.load_ips)):
            f = self.async_stress(cmd_list[i], load_index=i)
            futures.append(f)
            if i == 0:
                time.sleep(10)

        for f in futures:
            f.join()

        duration_seconds = time.time() - start_seconds
        print(f"Duration : {duration_seconds} seconds")
        print(f"Insertion rate: {item_count // duration_seconds} items/second")
        print(f"============== Inserting {item_count} items: done =======================")

    def __ssh(self, ip, command):
        self.__new_ssh(ip).exec(command)

    def ssh(self, command):
        run_parallel(self.__ssh, [(ip, command) for ip in self.load_ips])

    def __upload(self, ip, file):
        self.__new_ssh(ip).scp_to_remote(file, "")

    def upload(self, file):
        print("============== Upload: started ===========================")
        run_parallel(self.__upload, [(ip, file) for ip in self.load_ips])
        print("============== Upload: done ==============================")

    def __download(self, ip, dir):
        dest_dir = os.path.join(dir, ip)
        os.makedirs(dest_dir, exist_ok=True)
        print(f'    [{ip}] Downloading to [{dest_dir}]')
        self.__new_ssh(ip).scp_from_remote(f'*.{{html,hdr}}', dest_dir)
        print(f'    [{ip}] Downloading to [{dest_dir}] done')

    def collect_results(self, dir, warmup_seconds=None, cooldown_seconds=None):
        """
        Parameters
        ----------
        dir: str
            The download directory.
        warmup_seconds : str
            The warmup period in seconds. If the value is set, additional files will 
            be created where the warmup period is trimmed.
        cooldown_seconds : str
            The cooldown period in seconds. If the value is set, additional files will 
            be created where the cooldown period is trimmed.            
        """

        print("============== Getting results: started ===========================")
        run_parallel(self.__download, [(ip, dir) for ip in self.load_ips])
        hdrLogProcessor = HdrLogProcessor(self.properties, warmup_seconds=warmup_seconds, cooldown_seconds=cooldown_seconds)
        hdrLogProcessor.trim_recursivly(dir)
        hdrLogProcessor.merge_recursivly(dir)
        hdrLogProcessor.process_recursivly(dir)
        hdrLogProcessor.summarize_recursivly(dir)        
        print("============== Getting results: done ==============================")

    def __prepare(self, ip):
        print(f'    [{ip}] Preparing: started')
        ssh = self.__new_ssh(ip)
        ssh.exec(f'rm -fr *.html *.hdr')
        # we need to make sure that the no old load generator is still running.
        ssh.exec(f'killall -q -9 java')
        print(f'    [{ip}] Preparing: done')

    def prepare(self):
        print('============== Preparing load generator: started ===================')
        run_parallel(self.__prepare, [(ip,) for ip in self.load_ips])
        print('============== Preparing load generator: done ======================')
