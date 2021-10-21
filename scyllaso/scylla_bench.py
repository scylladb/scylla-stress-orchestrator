import os
import time

from datetime import datetime

from scyllaso.hdr import HdrLogProcessor
from scyllaso.ssh import SSH
from scyllaso.util import run_parallel, WorkerThread, log_important, log_machine, log


class ScyllaBench:

    def __init__(self, load_ips, properties, performance_governor=True):
        self.properties = properties
        self.load_ips = load_ips
        self.performance_governor = performance_governor
        self.ssh_user = properties.get('loadgenerator_user')

        # needed for compatibility reasons.
        if not self.ssh_user:
            self.ssh_user = properties.get('load_generator_user')

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.properties['ssh_options'])

    def __install(self, ip):
        ssh = self.__new_ssh(ip)
        log_machine(ip, f'Installing scylla_bench: started')
        ssh.update()

        if self.performance_governor:
            ssh.set_governor("performance")

        ssh.install("golang")
        # ssh.exec("go get github.com/scylladb/scylla-bench")

        ssh.exec(f"""
                  git clone https://github.com/scylladb/scylla-bench
                  cd scylla-bench/
                  go install .
                  """)

        log_machine(ip, f'Installing scylla_bench: done')

    def install(self):
        log_important("Installing scylla_bench: started")
        run_parallel(self.__install, [(ip,) for ip in self.load_ips])
        log_important("Installing scylla_bench: done")

    def __stress(self, ip, cmd):
        full_cmd = f'go/bin/scylla-bench {cmd}'

        dt = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        full_cmd = full_cmd + f" 2>&1 | tee -a scylla-bench-{dt}.log"
        log(full_cmd)
        self.__new_ssh(ip).exec(full_cmd)

    def stress(self, command, load_index=None):
        if load_index is None:
            log_important("scylla-bench: started")
            run_parallel(self.__stress, [(ip, command) for ip in self.load_ips])
            log_important("scylla-bench: done")
        else:
            log("using load_index " + str(load_index))
            self.__stress(self.load_ips[load_index], command)

    def async_stress(self, command, load_index=None):
        thread = WorkerThread(self.stress, (command, load_index))
        thread.start()
        return thread.future

    def insert(self,
               partition_count,
               nodes,
               partition_offset=0,
               concurrency=64,
               clustering_row_count=1,
               extra_args=""):
        log_important(f"Inserting {partition_count} partitions")
        start_seconds = time.time()

        # todo: there could be some loss if there is a reaminer.
        pc_per_lg = partition_count // len(self.load_ips)

        cmd_list = []
        for i in range(0, len(self.load_ips)):
            cmd = f"""-workload sequential \
                      -clustering-row-count {clustering_row_count} \
                      -mode write \
                      -partition-count {pc_per_lg} \
                      -partition-offset {partition_offset} \
                      -nodes {nodes} \
                      -concurrency {concurrency} \ 
                      {extra_args}"""
            # clean the string up.
            cmd = " ".join(cmd.split())
            cmd_list.append(cmd)
            partition_offset = partition_offset + pc_per_lg

        futures = []
        for i in range(0, len(self.load_ips)):
            f = self.async_stress(cmd_list[i], load_index=i)
            futures.append(f)
            if i == 0:
                # first one is given some extra time to set up the tables and all that.
                time.sleep(10)

        for f in futures:
            f.join()

        duration_seconds = time.time() - start_seconds
        log(f"Duration : {duration_seconds} seconds")
        log(f"Insertion rate: {partition_count // duration_seconds} items/second")
        log_important(f"Inserting {partition_count} partitions: done")

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
        ssh.scp_from_remote(f'*.{{hdr,log}}', dest_dir)
        ssh.exec(f'rm -fr *.hdr *.log')
        log_machine(ip, f'Collecting to [{dest_dir}] done')

    def collect_results(self, dir, warmup_seconds=None, cooldown_seconds=None):
        """
        Parameters
        ----------
        dir: str
            The download directory.
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
        ssh.exec(f'killall -q -9 go/bin/scylla-bench')
        log_machine(ip, f'Preparing: done')

    def prepare(self):
        log_important(f"Preparing load generator: started")
        run_parallel(self.__prepare, [(ip,) for ip in self.load_ips])
        log_important(f"Preparing load generator: done")
