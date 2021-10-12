import os
from datetime import datetime
from scyllaso.ssh import SSH
from scyllaso.util import run_parallel, log_important, log_machine, log


class Fio:

    def __init__(self, ips, ssh_user, ssh_options, capture_lsblk=True):
        self.ips = ips
        self.ssh_user = ssh_user
        self.ssh_options = ssh_options
        self.dir_name = "fio-" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.capture_lsblk = capture_lsblk

    def __new_ssh(self, ip):
        return SSH(ip, self.ssh_user, self.ssh_options)

    def __upload(self, ip, file):
        ssh = self.__new_ssh(ip)
        ssh.exec(f"mkdir -p {self.dir_name}")
        ssh.scp_to_remote(file, self.dir_name)

    def upload(self, file):
        log_important(f"Upload: started")
        run_parallel(self.__upload, [(ip, file) for ip in self.ips])
        log_important(f"Upload-Stress: done")

    def __install(self, ip):
        log_machine(ip, 'Installing fio: started')
        ssh = self.__new_ssh(ip)
        ssh.update()
        ssh.install('fio')
        log_machine(ip, 'Installing fio: done')

    def install(self):
        log_important(f"fio Installation: started")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        log_important(f"fio Installation: done")

    def __run(self, ip, options):
        log_machine(ip, 'fio: started')
        ssh = self.__new_ssh(ip)
        if self.capture_lsblk:
            ssh.exec(f'lsblk > lsblk.txt')

        ssh.exec(f"""
            mkdir -p {self.dir_name}
            cd {self.dir_name}
            sudo fio {options}            
            """)
        log_machine(ip, 'fio: done')

    def run(self, options):
        log_important(f"fio run: started")
        log(f"sudo fio {options}")
        run_parallel(self.__run, [(ip, options) for ip in self.ips])
        log_important(f"fio run: done")

    def __download(self, ip, dir):
        dest_dir = os.path.join(dir, ip)
        os.makedirs(dest_dir, exist_ok=True)

        log_machine(ip, f'Downloading to [{dest_dir}]')
        ssh = self.__new_ssh(ip)
        ssh.scp_from_remote(f'{self.dir_name}/*', dest_dir)
        if self.capture_lsblk:
            self.__new_ssh(ip).scp_from_remote(f'lsblk.out', dest_dir)

        log_machine(ip, f'Downloading to [{dest_dir}] done')

    def download(self, dir):
        log_important(f"fio download: started")
        run_parallel(self.__download, [(ip, dir) for ip in self.ips])
        log_important(f"fio download: done")
