import enum
import shlex
import subprocess
import selectors
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


def run_parallel(target, args_list, ignore_errors=False):
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


def call(cmd):
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sel = selectors.DefaultSelector()
    sel.register(process.stdout, selectors.EVENT_READ)
    sel.register(process.stderr, selectors.EVENT_READ)

    while True:
        for key, _ in sel.select():
            data = key.fileobj.read1().decode()

            if not data:
                return process.poll()
            lines = data.splitlines()
            log_level = LogLevel.info if key.fileobj is process.stdout else LogLevel.error
            for line in lines:
                log(line, log_level)


class LogLevel(enum.Enum):
    info = 1
    error = 2


def log_machine(ip, text, log_level=LogLevel.info):
    prefix = "    " + f"[{ip}]".ljust(17, " ")
    dt = datetime.now().strftime("%H:%M:%S")
    level_txt = level_text(log_level)
    print(f"{dt} {level_txt} {prefix} {text}")


def level_text(log_level):
    level_txt = "INFO "
    if log_level == LogLevel.error:
        level_txt = "ERROR"
    return level_txt


def log(text, log_level=LogLevel.info):
    dt = datetime.now().strftime("%H:%M:%S")
    level_txt = level_text(log_level)
    print(f"{dt} {level_txt} {text}")


def log_important(text):
    l = 80 - len(text)
    if l > 0:
        s = '-' * l
    else:
        s = ''
    log(f"-------------[ {text} ]{s}-----")
