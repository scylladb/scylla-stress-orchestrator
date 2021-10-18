import os
import time

from datetime import datetime
from scyllaso.hdr import HdrLogProcessor
from scyllaso.ssh import SSH
from scyllaso.util import run_parallel, WorkerThread, log_important, log_machine, log, WorkerThreadLoop


class CassandraStress:

    def __init__(self, load_ips, properties, scylla_tools=True, performance_governor=True):
        self.properties = properties
        self.load_ips = load_ips
        self.ssh_user = properties.get('loadgenerator_user')

        # needed for compatibility reasons.
        if not self.ssh_user:
            self.ssh_user = properties.get('load_generator_user')

        self.scylla_tools = scylla_tools
        self.performance_governor = performance_governor

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)
        ssh.update()

        if self.performance_governor:
            ssh.set_governor("performance")

        if self.scylla_tools:
            log_machine(ip, f'Installing cassandra-stress (Scylla): started')
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
            log_machine(ip, f'Installing cassandra-stress (Cassandra): started')
            cassandra_version = self.properties['cassandra_version']
            ssh.install_one('openjdk-8-jdk', 'java-1.8.0-openjdk')
            ssh.install('wget')
            ssh.exec(f"""
                set -e
                wget -q -N https://mirrors.netix.net/apache/cassandra/{cassandra_version}/apache-cassandra-{cassandra_version}-bin.tar.gz
                tar -xzf apache-cassandra-{cassandra_version}-bin.tar.gz
            """)

        log_machine(ip, f'Installing cassandra-stress: done')

    def install(self):
        log_important("Installing Cassandra-Stress: started")
        run_parallel(self.__install, [(ip,) for ip in self.load_ips])
        log_important("Installing Cassandra-Stress: done")

    def __stress(self, ip, startup_delay, cmd):
        time.sleep(startup_delay)

        if self.scylla_tools:
            full_cmd = f'cassandra-stress {cmd}'
        else:
            cassandra_version = self.properties['cassandra_version']
            cassandra_stress_dir = f'apache-cassandra-{cassandra_version}/tools/bin'
            full_cmd = f'{cassandra_stress_dir}/cassandra-stress {cmd}'

        dt = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        full_cmd = full_cmd + f" 2>&1 | tee -a cassandra-stress-{dt}.log"
        log(full_cmd)
        self.__new_ssh(ip).exec(full_cmd)

    def stress(self, command, load_index=None):
        if load_index is None:
            log_important("Cassandra-Stress: started")
            run_parallel(self.__stress, [(ip, 10 if i > 0 else 0, command) for i, ip in enumerate(self.load_ips)])
            log_important("Cassandra-Stress: done")
        else:
            log("using load_index " + str(load_index))
            self.__stress(self.load_ips[load_index], 0, command)

    def stress_seq_range(self, row_count, command_part1, command_part2):
        load_ip_count = len(self.load_ips)
        row_count_per_ip = row_count // load_ip_count
        range_points = [1]
        for i in range(load_ip_count):
            range_points.append(range_points[-1] + row_count_per_ip)
        range_points[-1] = row_count

        population_commands = []
        # FIXME - cleanup
        for i in range(len(range_points) - 1):
            population_commands.append(
                f' n={range_points[i + 1] - range_points[i] + 1} -pop seq={range_points[i]}..{range_points[i + 1]} ')

        print(population_commands)

        log_important("Cassandra-Stress: started")
        run_parallel(self.__stress,
                     [(ip, 10 if i > 0 else 0, command_part1 + pop_command + command_part2) for i, (ip, pop_command) in
                      enumerate(zip(self.load_ips, population_commands))])
        log_important("Cassandra-Stress: done")

    def async_stress(self, command, load_index=None):
        thread = WorkerThread(self.stress, (command, load_index))
        thread.start()
        return thread.future

    def loop_stress(self, command, load_index=None):
        thread = WorkerThreadLoop(self.stress, (command, load_index))
        thread.start()
        return thread

    def insert(self, profile, item_count, nodes, mode="native cql3", rate="threads=100", sequence_start=None):
        log_important(f"Inserting {item_count} items")
        start_seconds = time.time()

        per_load_generator = item_count // len(self.load_ips)
        start = sequence_start
        if sequence_start is None:
            start = 1

        end = start + per_load_generator - 1
        cmd_list = []
        for i in range(0, len(self.load_ips)):
            cmd = f'user profile={profile} "ops(insert=1)" n={per_load_generator} no-warmup -pop seq={start}..{end} -mode {mode} -rate {rate}  -node {nodes}'
            log(self.load_ips[i] + " " + cmd)
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
        log(f"Duration : {duration_seconds} seconds")
        log(f"Insertion rate: {item_count // duration_seconds} items/second")
        log_important(f"Inserting {item_count} items: done")

    def __ssh(self, ip, command):
        self.__new_ssh(ip).exec(command)

    def ssh(self, command):
        run_parallel(self.__ssh, [(ip, command) for ip in self.load_ips])

    def __upload(self, ip, file):
        self.__new_ssh(ip).scp_to_remote(file, "")

    def upload(self, file):
        log_important(f"Upload: started")
        run_parallel(self.__upload, [(ip, file) for ip in self.load_ips])
        log_important(f"Upload: done")

    def __collect(self, ip, dir):
        dest_dir = os.path.join(dir, ip)
        os.makedirs(dest_dir, exist_ok=True)
        log_machine(ip, f'Collecting to [{dest_dir}]')
        ssh = self.__new_ssh(ip)
        ssh.scp_from_remote(f'*.{{html,hdr,log}}', dest_dir)
        ssh.exec(f'rm -fr *.html *.hdr *.log')
        log_machine(ip, f'Collecting to [{dest_dir}] done')

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

        log_important(f"Collecting results: started")
        run_parallel(self.__collect, [(ip, dir) for ip in self.load_ips])
        p = HdrLogProcessor(self.properties, warmup_seconds=warmup_seconds, cooldown_seconds=cooldown_seconds)
        p.trim_recursivly(dir)
        p.merge_recursivly(dir)
        p.process_recursivly(dir)
        p.summarize_recursivly(dir)
        log_important(f"Collecting results: done")
        log(f"Results can be found in [{dir}]")

    def __prepare(self, ip):
        log_machine(ip, f'Preparing: started')
        ssh = self.__new_ssh(ip)
        # we need to make sure that the no old load generator is still running.
        ssh.exec(f'killall -q -9 java')
        log_machine(ip, f'Preparing: done')

    def prepare(self):
        log_important(f"Preparing load generator: started")
        run_parallel(self.__prepare, [(ip,) for ip in self.load_ips])
        log_important(f"Preparing load generator: done")
