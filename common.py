 
#!/bin/python3

import os
import ast
import subprocess
import yaml
import glob
import csv
from datetime import datetime
from threading import Thread


def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

class Iteration:
    def __init__(self, trial_name):
        self.trials_dir_name = "trials"
        self.trials_dir = os.path.join(os.getcwd(), self.trials_dir_name)
        self.trial_name = trial_name
        self.trial_dir = os.path.join(self.trials_dir, trial_name)

        self.name = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.dir = os.path.join(self.trial_dir, self.name)

        os.makedirs(self.dir)  
        
        latest_dir = os.path.join(self.trial_dir, "latest")
        if os.path.isdir(latest_dir): 
            os.unlink(latest_dir)
        os.symlink(self.dir, latest_dir, target_is_directory=True)            
        print(f'Using iteration directory [{self.dir}]')
        

class HdrLogMerging:
    def __init__(self, properties):
        self.properties = properties
    
    #def __log_merging(self, files):
        
    def merge_logs(self, dir):  
        print("------------------ HdrLogMerging -------------------------------------")
        print(dir)
        # todo be careful with merging the merge file.
        files_map = {}
        
        for hdr_file in glob.iglob(dir + '/*/*.hdr', recursive=True):
            print(hdr_file)
            base=os.path.splitext(os.path.basename(hdr_file))[0]
            files = files_map.get(base)
            if files == None:
                files = []
                files_map[base]=files
            files.append(hdr_file)    
        
        cwd = os.getcwd()
        jvm_path = self.properties['jvm_path']
        for name,files in files_map.items():            
            input = ""
            for file in files:
                input = input +" -ifp "+file
            cmd = f'{jvm_path}/bin/java -cp {cwd}/lib/processor.jar CommandDispatcherMain union {input} -of {dir}/{name}.hdr'
            print(cmd)
            os.system(cmd)
            
        print("------------------ HdrLogMerging -------------------------------------")
        

class HdrLogProcessor:
    def __init__(self, properties):
        self.properties = properties
        
    def process(self, dir):
        print("process "+str(dir))
        for hdr_file in glob.iglob(dir + '/**/*.hdr', recursive=True):
            print(hdr_file)
            self.__process(hdr_file)
            
    def __process(self, file):
        print("------------------ HdrLogProcessor -------------------------------------")
        filename = os.path.basename(file)
        filename_no_ext = os.path.splitext(filename)[0]
        jvm_path = self.properties['jvm_path']
        old_cwd = os.getcwd()
        new_cwd = os.path.dirname(os.path.realpath(file))
        os.chdir(new_cwd)
        
        tags = set()
        with open(filename, "r") as hdr_file:
            reader = csv.reader(hdr_file, delimiter=',')
            # Skip headers
            for i in range(5):
                next(reader, None)
            for row in reader:
                first_column = row[0]
                tag = first_column[4:]
                tags.add(tag)
         
        for tag in tags:
            os.system(f'{jvm_path}/bin/java -cp {old_cwd}/lib/HdrHistogram-2.1.9.jar org.HdrHistogram.HistogramLogProcessor -i {filename} -o {filename_no_ext+"_"+tag} -csv -tag {tag}')
        
        os.chdir(old_cwd)
        print("------------------ HdrLogProcessor -------------------------------------")
    
def run_parallel(t, args_list):
    threads = []
    for a in args_list:
        thread = Thread(target=t, args = a)
        thread.start()
        threads.append(thread)    
    for thread in threads:
        thread.join()

class Ssh:
    log_ssh = False
    
    def __init__(self, ip, user, ssh_options):
        self.ip = ip
        self.user = user
        self.ssh_options = ssh_options
        
    def scp_from_remote(self, src, dst):    
        cmd = f'scp {self.ssh_options} -q {self.user}@{self.ip}:{src} {dst}'
        if(self.log_ssh):
            print(cmd)
        os.system(cmd) 
    
    def scp_to_remove(self, src, dst):    
        cmd = f'scp {self.ssh_options} -q {src} {self.user}@{self.ip}:{dst}'
        if(self.log_ssh):
            print(cmd)
        os.system(cmd) 
    
    def run(self, command):
        cmd = f'ssh {self.ssh_options} {self.user}@{self.ip} \'{command}\''
        if self.log_ssh:
            print(cmd)
        os.system(cmd)

    def update(self):
        self.run(
            f"""if hash apt-get 2>/dev/null; then
                sudo apt-get -y -qq update
            elif hash yum 2>/dev/null; then
                sudo yum -y -q update
            else
                echo "Cannot update: no yum/apt"
                return 1
            fi""")

    def install_one(self, packages):
        for package in packages:
            self.install(package)
     
    def install(self, package):
        print(f'    [{self.ip}] Install: {package}')
        self.run(
            f"""if hash apt-get 2>/dev/null; then
                sudo apt-get install -y -qq {package}
            elif hash yum 2>/dev/null; then
                sudo yum -y -q install {package}
            else
                echo "Cannot install {package}: no yum/apt"
                return 1
            fi""")
     
class DiskExplorer:    
    
    def __init__(self, ips, ssh_user, ssh_options):        
        self.ips = ips
        self.ssh_user = ssh_user
        self.ssh_options = ssh_options
       
    def __install(self, ip):
        print(f'    [{ip}] Instaling disk-explorer: started')
        ssh = new_ssh(ip)
        ssh.update()
        ssh.install('git')
        ssh.install('fio')
        ssh.install('python3')
        ssh.install('python3-matplotlib')        
        ssh.run(f'rm -fr diskplorer')
        ssh.run(f'git clone https://github.com/scylladb/diskplorer.git')
        print(f'    [{ip}] Instaling disk-explorer: done')   

    def new_ssh(self, ip):
        return Ssh(ip, self.ssh_user, self.ssh_options)
        
    def install(self):
        print("============== Disk Explorer Installation: started =================")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        print("============== Disk Explorer Installation: done =================")

    def __run(self, ip, cmd):
        print(f'    [{ip}] Run: started')
        ssh = self.new_ssh(ip)
        ssh.run('rm -fr diskplorer/*.svg')
        ssh.run(f'cd diskplorer && python3 diskplorer.py {cmd}')
        # the file is 100 GB; so we want to remove it.
        ssh.run(f'rm -fr diskplorer/fiotest.tmp')
        print(f'    [{ip}] Run: done')

    def run(self, command):
        print("============== Disk Explorer run: started ===========================")
        print(f"diskplorer.py {command}")
        run_parallel(self.__run, [(ip, command) for ip in self.ips])    
        print("============== Disk Explorer run: done ===========================")

    def __download(self, ip, dir):
        dest_dir=os.path.join(dir, ip)
        os.makedirs(dest_dir)
        
        print(f'    [{ip}] Downloading to [{dest_dir}]')
        self.new_ssh(ip).scp_from_remote(f'diskplorer/*.{{svg,csv}}', dest_dir)
        print(f'    [{ip}] Downloading to [{dest_dir}] done')
    
    def download(self, dir):
        print("============== Disk Explorer Download: started ===========================")
        run_parallel(self.__download, [(ip, dir) for ip in self.ips])    
        print("============== Disk Explorer Download: done ===========================")


class CassandraStress:
    
    def __init__(self, ips, properties):        
        self.properties = properties
        self.ips = ips
        self.cassandra_version = properties['cassandra_version']
        self.ssh_user = properties['load_generator_user']
       
    def new_ssh(self, ip):
        return Ssh(ip, self.ssh_user, self.properties['ssh_options'])
                
    def __install(self, ip):
        print(f'    [{ip}] Instaling cassandra-stress: started')
        ssh = self.new_ssh(ip)
        ssh.update()
        ssh.install_one(['java-1.8.0-openjdk','openjdk-8-jdk'])                    
        ssh.install('wget')
        ssh.run(f'wget -q -N https://mirrors.netix.net/apache/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        ssh.run(f'tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        print(f'    [{ip}] Instaling cassandra-stress: done')   

    def install(self):
        print("============== Instaling Cassandra-Stress: started =================")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        print("============== Instaling Cassandra-Stress: done =================")

    def __stress(self, ip, cmd):
        print(cmd)
        cassandra_stress_dir=f'apache-cassandra-{self.cassandra_version}/tools/bin'
        full_cmd=f'{cassandra_stress_dir}/cassandra-stress {cmd}'
        self.new_ssh(ip).run(full_cmd)

    def stress(self, command):
        print("============== Cassandra-Stress: started ===========================")
        run_parallel(self.__stress, [(ip, command) for ip in self.ips])    
        print("============== Cassandra-Stress: done ==============================")

    def __ssh(self, ip, command):
        self.new_ssh(ip).run(command)
        
    def ssh(self, command):
        run_parallel(self.__ssh, [(ip, command) for ip in self.ips])    
        
    def __upload(self, ip, file):
        os.system(f'scp {self.ssh_options} -q {file} {self.user}@{ip}:')    
    
    def upload(self, file):
        print("============== Upload: started ===========================")
        run_parallel(self.__upload, [(ip, file) for ip in self.ips])    
        print("============== Upload-Stress: done ==============================")
    
    def __download(self, ip, dir):
        dest_dir=os.path.join(dir, ip)
        os.makedirs(dest_dir)
        print(f'    [{ip}] Downloading to [{dest_dir}]')
        self.new_ssh(ip).scp_from_remote(f'*.{{html,hdr}}', dest_dir)  
        print(f'    [{ip}] Downloading to [{dest_dir}] done')
    
    def get_results(self, dir):
        print("============== Getting results: started ===========================")
        run_parallel(self.__download, [(ip, dir) for ip in self.ips])                          
        HdrLogMerging(self.properties).merge_logs(dir)
        HdrLogProcessor(self.properties).process(dir)        
        print("============== Getting results: done ==============================")
                 
    def __prepare(self, ip):
        print(f'    [{ip}] Preparing: started')
        ssh = self.new_ssh(ip)
        ssh.run(f'rm -fr *.html *.hdr')
        # we need to make sure that the no old load generator is still running.
        ssh.run(f'killall -q -9 java')    
        print(f'    [{ip}] Preparing: done')

    def prepare(self):
        print('============== Preparing load generator: started ===================')
        run_parallel(self.__prepare, [(ip, ) for ip in self.ips])                              
        print('============== Preparing load generator: done ======================')    
