import os
import subprocess 
import glob
import csv

class HdrLogMerger:
    
    def __init__(self, properties):
        self.properties = properties        

    def merge(self, dir):
        print("------------------ HdrLogMerger -------------------------------------")
        print(dir)
        # todo be careful with merging the merge file.
        files_map = {}

        for hdr_file in glob.iglob(dir + '/*/*.hdr', recursive=True):
            print(hdr_file)
            base = os.path.splitext(os.path.basename(hdr_file))[0]
            files = files_map.get(base)
            if files is None:
                files = []
                files_map[base] = files
            files.append(hdr_file)

        lib_dir=f"{os.environ['SSO']}/lib/"    
        cwd = os.getcwd()
        jvm_path = self.properties['jvm_path']
        for name, files in files_map.items():
            input = ""
            for file in files:
                input = input + " -ifp " + file
            cmd = f'{jvm_path}/bin/java -cp {lib_dir}/processor.jar CommandDispatcherMain union {input} -of {dir}/{name}.hdr'
            print(cmd)
            os.system(cmd)

        print("------------------ HdrLogMerger -------------------------------------")


class HdrLogProcessor:
    
    def __init__(self, properties):
        self.properties = properties

    def process(self, dir):
        print("process " + str(dir))
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

        lib_dir=f"{os.environ['SSO']}/lib/"
        print("lib dir = "+lib_dir)
        for tag in tags:
            os.system(
                f'{jvm_path}/bin/java -cp {lib_dir}/HdrHistogram-2.1.9.jar org.HdrHistogram.HistogramLogProcessor -i {filename} -o {filename_no_ext + "_" + tag} -csv -tag {tag}')

        os.system(
            f'{jvm_path}/bin/java -cp {lib_dir}/processor.jar CommandDispatcherMain summarize -if {filename_no_ext}.hdr >  {filename_no_ext}-summary.txt')

        os.chdir(old_cwd)
        print("------------------ HdrLogProcessor -------------------------------------")
