import os
from datetime import datetime
from scyllaso.ssh import SSH
from scyllaso.util import run_parallel, log, log_important, log_machine


class DiskExplorer:

    def __init__(self, ips, ssh_user, ssh_options, capture_lsblk=True):
        self.ips = ips
        self.ssh_user = ssh_user
        self.ssh_options = ssh_options
        self.capture_lsblk = capture_lsblk

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.ssh_options)

    def __install(self, ip):
        log_machine(ip, 'Installing disk-explorer: started')
        ssh = self.__new_ssh(ip)
        ssh.update()
        ssh.install('git', 'fio', 'python3', 'python3-pip')
        ssh.exec(f"""
            sudo pip3 install -qqq matplotlib
            rm -fr diskplorer
            git clone -q https://github.com/scylladb/diskplorer.git
            """)
        log_machine(ip, 'Installing disk-explorer: done')

    def install(self):
        log_important("Disk Explorer Installation: started")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        log_important("Disk Explorer Installation: done")

    def __run(self, ip, cmd):
        log_machine(ip, 'Run: started')
        ssh = self.__new_ssh(ip)
        ssh.exec('rm -fr diskplorer/*.svg')
        ssh.exec(f'rm -fr diskplorer/fiotest.tmp')
        if self.capture_lsblk:
            ssh.exec(f'lsblk > lsblk.out')
        ssh.exec(f"""
            ulimit -n 64000            
            ulimit -n
            ulimit -Sn 64000
            ulimit -Sn
            cd diskplorer                 
            python3 diskplorer.py {cmd}
            """)
        # the file is 100 GB; so we want to remove it.
        ssh.exec(f'rm -fr diskplorer/fiotest.tmp')
        log_machine(ip, 'Run: done')

    def run(self, command):
        log_important(f'Disk Explorer run: started [{datetime.now().strftime("%H:%M:%S")}]')
        log(f"python3 diskplorer.py {command}")
        run_parallel(self.__run, [(ip, command) for ip in self.ips])
        log_important(f'Disk Explorer run: done [{datetime.now().strftime("%H:%M:%S")}]')


def __download(self, ip, dir):
    dest_dir = os.path.join(dir, ip)
    os.makedirs(dest_dir, exist_ok=True)

    log_machine(ip, f'[{ip}] Downloading to [{dest_dir}]')
    self.__new_ssh(ip).scp_from_remote(f'diskplorer/*.{{svg,csv}}', dest_dir)
    if self.capture_lsblk:
        self.__new_ssh(ip).scp_from_remote(f'lsblk.out', dest_dir)
    log_machine(ip, f'Downloading to [{dest_dir}] done')


def download(self, dir):
    log_important("Disk Explorer Download: started")
    run_parallel(self.__download, [(ip, dir) for ip in self.ips])
    log_important("Disk Explorer Download: done")
    log(f"Results can be found in [{dir}]")
