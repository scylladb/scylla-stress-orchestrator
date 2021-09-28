from datetime import datetime
from threading import Thread
from threading import Lock, Condition
 
class Future:
    def __init__(self):
        self.__condition = Condition(Lock())
        self.__val = None
        self.__is_set = False

    def get(self):
        with self.__condition:
            while not self.__is_set:
                self.__condition.wait()
                
            if self.__val is Exception:
                 raise Exception() from self.__val
            return self.__val

    def join(self):
        self.get()

    def set(self, val):
        with self.__condition:
            if self.__is_set:
                raise RuntimeError("Future has already been set")
            self.__val = val
            self.__is_set = True
            self.__condition.notify_all()

    def done(self):
        return self.__is_set
 
class WorkerThread(Thread):
    
    def __init__(self, target, args):
        super().__init__(target=target, args=args)
        self.future = Future()
        
    def run(self):
        self.exception = None 
        try:
             super().run()
             self.future.set(True)
        except Exception as e:
            self.exception = e    
            self.future.set(e)


def run_parallel(target, args_list, ignore_errors = False):
    # print(f"parallel{type(args_list)}")
    # print(args_list)
    threads = []
    for args in args_list:
        # print(f"run_parallel loop |{args}|")
        # print(f"type {type(args)}")
        thread = WorkerThread(target, args)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
        if not ignore_errors and thread.exception:
            raise Exception() from thread.exception

def find_java(properties):
    path = properties.get("jvm_path")
    if path:
        return f"{path}/bin/java"
    from shutil import which
    path = which("java")
    if path:
        return path
    else:
        raise RuntimeError("Could not locate java")

def join_all(*futures):
    for f in futures:
        f.join()
      
def log_machine(ip, text):
    prefix = "    "+f"[{ip}]".ljust(17, " ")
    print(f"{prefix} {text}")    

def log_important(text):
    l = 80 -len(text)
    if l > 0:
        s = '-' * l
    else:
        s = ''
    dt = datetime.now().strftime("%H:%M:%S")
    print(f"[{dt}]-------------[ {text} ]{s}-----")
