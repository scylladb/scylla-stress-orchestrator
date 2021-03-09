from threading import Thread
 
class WorkerThread(Thread):
    def __init__(self, target, args):
        super().__init__(target=target, args=args)

    def run(self):
        self.exception = None 
        try:
             super().run()
        except Exception as e:
            self.exception = e    

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
        

