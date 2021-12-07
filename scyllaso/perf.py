from scyllaso.ssh import PSSH, SSH
from scyllaso.util import log_important, log


#
# Support for running Linux Perf on remote machines and creating flame-graphs.
#
class Perf:

    def __init__(self, ip_list, user, ssh_options):
        log(ip_list)
        self.updated = False
        self.ip_list = ip_list
        self.user = user
        self.ssh_options = ssh_options

    def __pssh(self):
        return PSSH(self.ip_list, self.user, self.ssh_options)

    def install(self):
        # Install all dependencies required for running perf and making flame-graphs.
        self.__install_perf()
        self.__install_flamegraph()
        self.__install_scylla_debuginfo()

    def __install_scylla_debuginfo(self):
        # Install scylla debug info
        pssh = self.__pssh()

        if not self.updated:
            pssh.update()
            self.updated = True

        log_important("Installing debuginfo: started")
        pssh.try_install("scylla_debuginfo")
        log_important("Installing debuginfo: done")

    def __install_perf(self):
        log_important("Perf install: started")
        pssh = self.__pssh()

        if not self.updated:
            pssh.update()
            self.updated = True

        # This part sucks.. Should no be a dependency on a particular version 
        pssh.install_one("perf", "linux-tools-5.4.0-1035-aws")
        log_important("Perf install: done")

    def __install_flamegraph(self):
        log_important("Perf install flamegraph: started")
        pssh = self.__pssh()

        if not self.updated:
            pssh.update()
            self.updated = True

        pssh.install("git")
        # needed for addr2line
        pssh.install("binutils")
        pssh.exec(f"""
                cd /tmp
                if [ ! -d FlameGraph ]; then
                    echo "cloning flamegraph"
                    git clone https://github.com/brendangregg/FlameGraph
                fi
                """)
        log_important("Perf install flamegraph: done")

    def flamegraph_cpu(self, cpu, dir, duration_seconds=60, args="--call-graph lbr -F99", output="flamegraph"):
        # Creates a flamegraph based on 'perf record -C <cpu>'
        data_file = f"{output}.data"
        flamegraph_file = f"{output}.svg"
        cmd = f"--output {data_file} --cpu {cpu} {args} sleep {duration_seconds}"
        self.record(cmd)
        self.collect_flamegraph(dir, data_file, flamegraph_file)

    def list(self):
        # Runs 'perf list -v' on the remote machines to get an overview of the available events.
        self.exec("sudo perf list -v")

    def record(self, command):
        # Runs 'perf record <command>' on the remote machines.
        cmd = f"sudo perf record {command}"
        self.exec(cmd)

    def script(self, command):
        # Runs 'perf script <command>' on the remote machines.
        cmd = f"sudo perf script {command}"
        self.exec(cmd)

    def exec(self, command):
        log_important(f"Perf: started")
        log(command)
        ssh = SSH(self.ip_list[0], self.user, self.ssh_options)
        ssh.exec(f"""
                cd /tmp
                {command}
                """)
        log_important(f"Perf: done")

    def collect_flamegraph(self, dir, data_file="perf.data", flamegraph_file="flamegraph.svg"):
        # Collect the remotely created flame-graphs.
        log_important(f"Perf collecting flamegraph: started")
        ssh = SSH(self.ip_list[0], self.user, self.ssh_options)
        # --no-online
        ssh.exec(f"""
                cd /tmp
                sudo perf script -i {data_file} | FlameGraph/stackcollapse-perf.pl | FlameGraph/flamegraph.pl --hash > {flamegraph_file}
                """)
        ssh.scp_from_remote(f"/tmp/{flamegraph_file}", dir)
        ssh.exec(f"rm /tmp/{flamegraph_file}")
        log_important(f"Perf collecting flamegraph: done")
