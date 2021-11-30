from time import sleep
from datetime import datetime, timedelta
import socket

from scyllaso.ssh import SSH
from scyllaso.util import log_machine, log_important, run_parallel


class cqlsh:

    def __init__(self, ip_list, ssh_user, ssh_options, username=None, password=None):
        self.ip_list = ip_list
        self.ssh_user = ssh_user
        self.ssh_options = ssh_options
        self.username = username
        self.password = password
        self.wait_for_cql_start()

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.ssh_options)

    def __wait_for_cql_start(self, ip, timeout, connect_timeout, max_tries_per_second):
        wait_for_cql_start(ip, timeout,connect_timeout, max_tries_per_second)

    def wait_for_cql_start(self, timeout=7200, connect_timeout=10, max_tries_per_second=2):
        log_important(f"cql: wait for start")
        run_parallel(self.__wait_for_cql_start, [(ip, timeout, connect_timeout, max_tries_per_second) for ip in self.ip_list])
        log_important(f"cqlsh: running")

    def __exec(self, ip, cql):
        ssh = self.__new_ssh(ip)
        ssh.exec("touch foo.cql")
        ssh.exec(f"echo \"{cql}\" > foo.cql")
        cmd ="cqlsh "
        if self.username:
            cmd+=f"-u {self.username} "
        if self.password:
            cmd += f"-p {self.password} "
        cmd += "-f foo.cql"
        ssh.exec(cmd)

    def exec(self, cql):
        log_important(f"cqlsh exec: [{cql}]")
        run_parallel(self.__exec, [(ip,cql) for ip in self.ip_list])
        log_important(f"cqlsh done")


def wait_for_cql_start(node_ip, timeout=7200, connect_timeout=10, max_tries_per_second=2):
    log_machine(node_ip, 'Waiting for CQL port to start (meaning node bootstrap finished). This could take a while.')

    backoff_interval = 1.0 / max_tries_per_second
    timeout_point = datetime.now() + timedelta(seconds=timeout)

    feedback_interval = 20
    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)

    while datetime.now() < timeout_point:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(connect_timeout)
            try:
                sock.connect((node_ip, 9042))
            except:
                # There was a problem connecting to CQL port.
                sleep(backoff_interval)
                if datetime.now() > print_feedback_point:
                    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)
                    log_machine(node_ip, 'Still waiting for CQL port to start...')

            else:
                log_machine(node_ip, 'Successfully connected to CQL port.')
                return

    raise Exception(f'Waiting for CQL to start timed out after {timeout} seconds for node: {node_ip}.')
