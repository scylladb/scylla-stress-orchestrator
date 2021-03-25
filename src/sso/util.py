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
    threads = []
    for args in args_list:
        thread = WorkerThread(target, args)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
        if not ignore_errors and thread.exception:
            raise Exception() from thread.exception
    
    
def join_all(*futures):
    for f in futures:
        f.join()
      

def print_important(text):
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("                     "+text)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

