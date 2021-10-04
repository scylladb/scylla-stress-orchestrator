import os


def cli():
    scylla_monitoring_path = os.environ['SCYLLA_MONITORING']

    old_wd = os.getcwd()
    os.chdir(scylla_monitoring_path)
    cmd = f"./kill-all.sh"
    os.system(cmd)
    os.chdir(old_wd)
