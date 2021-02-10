 
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
        
class CassandraStress:
    ssh_options="-i key -o StrictHostKeyChecking=no"
    log_ssh = False
    
    def __init__(self, ips, properties):        
        self.properties = properties
        self.ips = ips
        self.cassandra_version = properties['cassandra_version']
        self.ssh_options = properties['ssh_options']
        self.user = properties['load_generator_user']
        
    def __install(self, ip):
        print(f'    [{ip}] Instaling cassandra-stress: started')
        self.__ssh(ip, f'sudo yum -y -q install java-1.8.0-openjdk')
        self.__ssh(ip, f'wget -q -N https://mirrors.netix.net/apache/cassandra/{self.cassandra_version}/apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        self.__ssh(ip, f'tar -xzf apache-cassandra-{self.cassandra_version}-bin.tar.gz')
        print(f'    [{ip}] Instaling cassandra-stress: done')   

    def install(self):
        print("============== Instaling Cassandra-Stress: started =================")
        run_parallel(self.__install, [(ip,) for ip in self.ips])
        print("============== Instaling Cassandra-Stress: done =================")

    def __stress(self, ip, cmd):
        print(cmd)
        cassandra_stress_dir=f'apache-cassandra-{self.cassandra_version}/tools/bin'
        full_cmd=f'{cassandra_stress_dir}/cassandra-stress {cmd}'
        self.__ssh(ip, full_cmd)

    def stress(self, command):
        print("============== Cassandra-Stress: started ===========================")
        run_parallel(self.__stress, [(ip, command) for ip in self.ips])    
        print("============== Cassandra-Stress: done ==============================")

    def __ssh(self, ip, command):
        if self.log_ssh:
            print(command)
        os.system(f'ssh {self.ssh_options} {self.user}@{ip} \'{command}\'')
    
    def ssh(self, command):
        #print(full_cmd)
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
        os.system(f'scp {self.ssh_options} -q {self.user}@{ip}:*.{{html,hdr}} {dest_dir}')    
        print(f'    [{ip}] Downloading to [{dest_dir}] done')
    
    def get_results(self, dir):
        print("============== Getting results: started ===========================")
        run_parallel(self.__download, [(ip, dir) for ip in self.ips])                          
        HdrLogMerging(self.properties).merge_logs(dir)
        HdrLogProcessor(self.properties).process(dir)        
        print("============== Getting results: done ==============================")
                 
    def __prepare(self, ip):
        print(f'    [{ip}] Preparing: started')
        self.__ssh(ip, f'rm -fr *.html *.hdr')
        # we need to make sure that the no old load generator is still running.
        self.__ssh(ip, f'killall -q -9 java')    
        print(f'    [{ip}] Preparing: done')

    def prepare(self):
        print('============== Preparing load generator: started ===================')
        run_parallel(self.__prepare, [(ip, ) for ip in self.ips])                              
        print('============== Preparing load generator: done ======================')    
