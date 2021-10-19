import os
import selectors
import subprocess
import time
from scyllaso.util import run_parallel, log_machine, LogLevel, WorkerThread


# Parallel SSH
class PSSH:

    def __init__(self,
                 ip_list,
                 user,
                 ssh_options,
                 use_control_socket=True,
                 silent_seconds=30,
                 log_ssh=False):
        self.ip_list = ip_list
        self.user = user
        self.ssh_options = ssh_options
        self.use_control_socket = use_control_socket
        self.silent_seconds = silent_seconds
        self.log_ssh = log_ssh

    def __new_ssh(self, ip):
        return SSH(ip,
                   self.user,
                   self.ssh_options,
                   use_control_socket=self.use_control_socket,
                   silent_seconds=self.silent_seconds,
                   log_ssh=self.log_ssh)

    def __exec(self, ip, cmd):
        self.__new_ssh(ip).exec(cmd)

    def exec(self, cmd):
        run_parallel(self.__exec, [(ip, cmd) for ip in self.ip_list])

    def async_exec(self, command):
        thread = WorkerThread(self.exec, (command))
        thread.start()
        return thread.future

    def __update(self, ip):
        self.__new_ssh(ip).update()

    def update(self):
        # todo: needs to be fixed; should be parallel, now sequential
        for ip in self.ip_list:
            ssh = SSH(ip, self.user, self.ssh_options)
            ssh.update()

        # can't get this to run correctly.
        # run_parallel(self.__update, [ip for ip in self.ip_list])

    def __install_one(self, ip, *packages):
        self.__new_ssh(ip).install_one(*packages)

    def install_one(self, *packages):
        run_parallel(self.__install_one, [(ip, *packages) for ip in self.ip_list])

    def __try_install(self, ip, *packages):
        self.__new_ssh(ip).try_install(*packages)

    def try_install(self, *packages):
        run_parallel(self.__try_install, [(ip, *packages) for ip in self.ip_list])

    def __install(self, ip, *packages):
        self.__new_ssh(ip).install(*packages)

    def install(self, *packages):
        run_parallel(self.__install, [(ip, *packages) for ip in self.ip_list])

    def __scp_from_remote(self, src, dst_dir, ip):
        self.__new_ssh(ip).scp_from_remote(src, os.path.join(dst_dir, ip))

    def scp_from_remote(self, src, dst_dir):
        run_parallel(self.__scp_from_remote, [(src, dst_dir, ip) for ip in self.ip_list])

    def __scp_to_remote(self, src, dst, ip):
        self.__new_ssh(ip).scp_to_remote(src, dst)

    def scp_to_remote(self, src, dst):
        run_parallel(self.__scp_to_remote, [(src, dst, ip) for ip in self.ip_list])

    def __set_governor(self, ip, governor):
        self.__new_ssh(ip).set_governor(governor)

    def set_governor(self, governor):
        run_parallel(self.__set_governor, [(ip, governor) for ip in self.ip_list])


class SSH:

    def __init__(self,
                 ip,
                 user,
                 ssh_options,
                 silent_seconds=30,
                 use_control_socket=True,
                 log_ssh=False):
        self.ip = ip
        self.user = user
        self.ssh_options = ssh_options
        self.silent_seconds = silent_seconds
        self.log_ssh = log_ssh
        if use_control_socket:
            self.control_socket_file = f"/tmp/{self.user}@{self.ip}.socket"
        else:
            self.control_socket_file = None

    def __wait_for_connect(self):
        args = f"-o ConnectTimeout=1 -o ConnectionAttempts=1 {self.ssh_options}"
        if self.control_socket_file:
            if os.path.exists(self.control_socket_file):
                return
            args = f"{args} -M -S {self.control_socket_file} -o ControlPersist=5m"
        cmd = f'ssh {args} {self.user}@{self.ip} exit'

        exitcode = None
        max_attempts = 300
        for attempt in range(1, max_attempts):
            if attempt > self.silent_seconds:
                log_machine(self.ip, f'Trying to connect, attempt [{attempt}/{max_attempts}], command [{cmd}]')
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    lines = result.stdout.splitlines()
                    for line in lines:
                        log_machine(self.ip, line, log_level=LogLevel.info)
                if result.stderr:
                    lines = result.stderr.splitlines()
                    for line in lines:
                        log_machine(self.ip, line, log_level=LogLevel.warning)
                exitcode = result.returncode
            else:
                exitcode = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if exitcode == 0 or exitcode == 1:  # todo: we need to deal better with exit code
                self.wait_for_connect = False
                return
            time.sleep(1)

        raise Exception(f"Failed to connect to {self.ip}, exitcode={exitcode}")

    def __is_connected(self):
        return self.control_socket_file and os.path.exists(self.control_socket_file)

    def scp_from_remote(self, src, dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
        cmd = f'scp {self.ssh_options} -r -q {self.user}@{self.ip}:{src} {dst_dir}'
        self.__scp(cmd)

    def scp_to_remote(self, src, dst):
        cmd = f'scp {self.ssh_options} -r -q {src} {self.user}@{self.ip}:{dst}'
        self.__scp(cmd)

    def __scp(self, cmd):
        self.__wait_for_connect()
        exitcode = subprocess.call(cmd, shell=True)
        # raise Exception(f"Failed to execute {cmd} after {self.max_attempts} attempts")

    def exec(self, command, ignore_errors=False):
        self.__wait_for_connect()

        cmd_list = ["ssh"]
        if self.__is_connected():
            cmd_list.append("-S")
            cmd_list.append(f"{self.control_socket_file}")
        cmd_list.extend(self.ssh_options.split())
        cmd_list.append(f"{self.user}@{self.ip}")
        cmd_list.append(command)

        if self.log_ssh:
            log_machine(self.ip, cmd_list)

        process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        sel = selectors.DefaultSelector()
        sel.register(process.stdout, selectors.EVENT_READ)
        sel.register(process.stderr, selectors.EVENT_READ)

        while True:
            for key, _ in sel.select():
                data = key.fileobj.read1().decode()
                if not data:
                    exitcode = process.poll()
                    if ignore_errors or exitcode == 0 or exitcode == 1:  # todo: we need to deal better with exit code
                        return
                    else:
                        raise Exception(f"Failed to execute [{cmd_list}], exitcode={exitcode}")
                lines = data.splitlines()
                log_level = LogLevel.info if key.fileobj is process.stdout else LogLevel.warning
                for line in lines:
                    log_machine(self.ip, line, log_level)

    def async_exec(self, command):
        thread = WorkerThread(self.exec, (command))
        thread.start()
        return thread.future

    def update(self):
        log_machine(self.ip, f'Update: started')
        self.exec(
            f"""
            set -e
            if [ -f /tmp/update.called ] ; then
                # echo "Skipping update"
                exit 0
            fi

            if hash apt-get 2>/dev/null; then
                sudo apt-get -y -qq update
            elif hash yum 2>/dev/null; then
                sudo yum -y -q update
            else
                echo "Cannot update: yum/apt not found"
                exit 1
            fi

            touch /tmp/update.called
            """)
        log_machine(self.ip, f'Update: done')

    def install_one(self, *packages):
        self.exec(
            f"""
            set -e
            for package in {" ".join(packages)} 
            do                
                echo Trying package [$package]
                if hash apt-get 2>/dev/null ; then
                    if sudo apt show $package >/dev/null 2>&1; then
                        echo      [{self.ip}] Installing $package
                        sudo apt-get install -y -qq $package
                        exit 0
                    fi    
                elif hash yum 2>/dev/null; then
                    if sudo yum info $package >/dev/null 2>&1; then
                        echo      [{self.ip}] Installing $package
                        sudo yum -y -q install $package
                        exit 0
                    fi                        
                else
                    echo "     [{self.ip}] Cannot install $package: yum/apt not found"
                    exit 1
                fi
                    
                echo Not found $package                       
            done
            echo "Could not find any of the packages from {packages}"
            exit 1
            """)

    def try_install(self, *packages):
        self.install(*packages, ignore_errors=True)

    def install(self, *packages, ignore_errors=False):
        for package in packages:
            log_machine(self.ip, f'Install: {package}')
            self.exec(
                f"""
                set -e
                if hash apt-get 2>/dev/null; then
                    sudo apt-get install -y -qq {package}
                elif hash yum 2>/dev/null; then
                    sudo yum -y -q install {package}
                else
                    echo "Cannot install {package}: yum/apt not found"
                    exit 1
                fi
                """, ignore_errors=ignore_errors)

    def set_file_property(self, file_path, property, seperator, value):
        self.exec(f"""
            set -e
            sudo touch {file_path}
            if grep -q -E "^\\s*{property}\\s*{seperator}.*" {file_path}; then 
                sudo sed -i "s/^\\s*{property}\\s*{seperator}.*/{property + seperator + value}/g" {file_path}
            else
                sudo sh -c "'echo {property + seperator + value}' >> {file_path}"
            fi
        """)

    def set_governor(self, governor):
        log_machine(self.ip, f'Set governor [{governor}]')
        self.exec(f"""
            set -e
    
            if ! hash cpupower 2>/dev/null; then
                echo "Installing cpupower"
                if hash apt-get 2>/dev/null; then
                    sudo apt-get -y -qq update
                    version=$(uname -r)
                    sudo apt-get -y -qq install linux-tools-$version
                    echo "apt-get found"                           
                elif hash yum 2>/dev/null; then
                    sudo yum -y -q install kernel-tools                
                else
                    echo "Cannot install {governor}: yum/apt not found"                
                    exit 1
                fi
            fi
            echo "=========== frequency info before change ==========="
            sudo cpupower frequency-info
            echo "===================================================="
            frequencyinfo=$(sudo cpupower frequency-info)                  
            if [[ $frequencyinfo =~ "{governor}" ]]; then
                sudo cpupower frequency-set -g {governor}  
                echo "=========== frequency info after change ==========="
                sudo cpupower frequency-info
                echo "===================================================="                      
            else
                echo "Skipping set governor, [{governor}] is not supported"
            fi             
        """)
