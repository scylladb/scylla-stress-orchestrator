from sso.ssh import PSSH,SSH
from sso.util import log_important

class Perf:

    def __init__(self, ip_list, user, ssh_options):
        print(ip_list)
        self.ip_list = ip_list
        self.user = user
        self.ssh_options = ssh_options

    def pssh(self):
        return PSSH(self.ip_list, self.user, self.ssh_options)

    def install(self):
        self.install_perf()
        self.install_flamegraph()
        self.install_debuginfo()

    def install_debuginfo(self):
        pssh = self.pssh()
        pssh.update()
        log_important("Installing debuginfo: started")
        pssh.try_install("scylla_debuginfo")
        log_important("Installing debuginfo: done")

    def install_perf(self):
        log_important("Perf install: started")
        pssh = self.pssh()
        pssh.update()
        pssh.install_one("perf", "linux-tools-5.4.0-1035-aws")        
        log_important("Perf install: done")

    def install_flamegraph(self):
        log_important("Perf install flamegraph: started")
        pssh = self.pssh()
        pssh.update()
        pssh.install("git")
        # needed for addr2line
        pssh.install("binutils")
        pssh.exec(f"""
                cd /tmp
                if [ ! -d FlameGraph ]; then
                    git clone --depth=1 https://github.com/brendangregg/FlameGraph
                fi
                """)
        log_important("Perf install flamegraph: done")

    def flamegraph_cpu(self, cpu, dir, duration_seconds=60):
        self.record(f"-o perf.data -C {cpu} --call-graph dwarf -F 99 sleep {duration_seconds}")
        self.collect_flamegraph(dir)

    def record(self, command):
        cmd = f"sudo perf record {command}"
        self.exec(cmd)

    def exec(self, command):
        log_important(f"Perf record: started")
        print(command)
        ssh = SSH(self.ip_list[0], self.user, self.ssh_options)
        ssh.exec(f"""
                cd /tmp
                {command}
                """)
        log_important(f"Perf record: done")

    def collect_flamegraph(self, dir):
        log_important(f"Perf collecting flamegraph: started")
        ssh = SSH(self.ip_list[0], self.user, self.ssh_options)
        ssh.exec(f"""
                cd /tmp
                sudo perf script -i perf.data --no-inline | FlameGraph/stackcollapse-perf.pl | FlameGraph/flamegraph.pl --hash > flamegraph.svg
                """)
        ssh.scp_from_remote("/tmp/flamegraph.svg", dir)
        ssh.exec("rm /tmp/flamegraph.svg")
        log_important(f"Perf collecting flamegraph: done")
