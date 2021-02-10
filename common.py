 
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
        

class HdrLogProcessor:
    def __init__(self, properties):
        self.properties = properties
        
    def process(self, dir):
        print("process "+str(dir))
        for hdr_file in glob.iglob(dir + '/**/*.hdr', recursive=True):
            print(hdr_file)
            self.__process(hdr_file)
            
    def __process(self, file):
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
            os.system(f'{jvm_path}/bin/java -cp {old_cwd}/lib/*.jar org.HdrHistogram.HistogramLogProcessor -i {filename} -o {filename_no_ext+"_"+tag} -csv -tag {tag}')
        
        os.chdir(old_cwd)
    
def run_parallel(t, args_list):
    threads = []
    for a in args_list:
        thread = Thread(target=t, args = a)
        thread.start()
        threads.append(thread)    
    for thread in threads:
        thread.join()
    
    
class CassandraStress:
    ssh_options="-i key -o StrictHostKeyChecking=no"
    
    def __init__(self, ips, properties):        
        self.properties = properties
        self.ips = ips
        self.cassandra_version = properties['cassandra_version']
        self.ssh_options = properties['ssh_options']
        self.user = properties['load_generator_user']
        
    def __install(self, ip):
        print(f'    [{ip}] Instaling cassandra-stress: started')
        self.ssh(ip, f'sudo yum -y -q install java-1.8.0-openjdk')
        self.ssh(ip, f'wget -q https://mirrors.netix.net/apache/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        self.ssh(ip, f'tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        print(f'    [{ip}] Instaling cassandra-stress: done')   

    def install(self):
        print("============== Instaling Cassandra-Stress: started =================")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        print("============== Instaling Cassandra-Stress: done =================")

    def __stress(self, ip, cmd):
        cassandra_stress_dir=f'apache-cassandra-{self.cassandra_version}/tools/bin'
        full_cmd=f'{cassandra_stress_dir}/cassandra-stress {cmd}'
        self.ssh(ip, full_cmd)

    def stress(self, command):
        print("============== Cassandra-Stress: started ===========================")
        run_parallel(self.__stress, [(ip, command) for ip in self.ips])    
        print("============== Cassandra-Stress: done ==============================")

    def ssh(self, ip, command):
        #print(full_cmd)
        os.system(f'ssh {self.ssh_options} {self.user}@{ip} "{command}"')
    
    def __download(self, ip, dir):
        dest_dir=os.path.join(dir, ip)
        os.makedirs(dest_dir)
        print(f'    [{ip}] Downloading to [{dest_dir}]')
        os.system(f'scp {self.ssh_options} -q {self.user}@{ip}:*.html {dest_dir}')
        os.system(f'scp {self.ssh_options} -q {self.user}@{ip}:*.hdr {dest_dir}')
        print(f'    [{ip}] Downloading to [{dest_dir}] done')
    
    def get_results(self, dir):
        print("============== Getting results: started ===========================")
        run_parallel(self.__download, [(ip, dir) for ip in self.ips])                          
        HdrLogProcessor(self.properties).process(dir)        
        print("============== Getting results: done ==============================")
                 
    def __prepare(self, ip):
        print(f'    [{ip}] Preparing: started')
        self.ssh(ip, f'rm -fr *.html')
        self.ssh(ip, f'rm -fr *.hdr')
        # we need to make sure that the no old load generator is still running.
        self.ssh(ip, f'killall -q -9 java')    
        print(f'    [{ip}] Preparing: done')

    def prepare(self):
        print('============== Preparing load generator: started ===================')
        run_parallel(self.__prepare, [(ip, ) for ip in self.ips])                              
        print('============== Preparing load generator: done ======================')    
