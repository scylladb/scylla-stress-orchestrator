import os
import yaml
import subprocess
import time
from datetime import datetime
from scyllaso.ssh import SSH
from scyllaso.util import run_parallel


def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class Iteration:

    # The purpose of the experimental flag is to modify the name of the trial directory to easily
    # weed out the experimental runs from non experimental ones. Otherwise it is easy to run in a 
    # messed up history where it isn't clear what is experimental and what isn't.
    def __init__(self, trial_name, description=None, experimental=False, ignore_git=True):
        self.trials_dir_name = "trials"
        self.trials_dir = os.path.join(os.getcwd(), self.trials_dir_name)
        self.trial_name = trial_name
        self.trial_dir = os.path.join(self.trials_dir, trial_name)

        while True:
            self.name = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            if experimental:
                self.name = self.name + "_experimental"
            self.dir = os.path.join(self.trial_dir, self.name)
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)
                break
            time.sleep(0.5)

        if description:
            desc_file = os.path.join(self.dir, "description.txt")
            with open(desc_file, "w") as text_file:
                print(description, file=text_file)

        if not experimental:
            latest_dir = os.path.join(self.trial_dir, "latest")
            if os.path.isdir(latest_dir):
                os.unlink(latest_dir)
            elif os.path.islink(latest_dir):
                # it is a broken sym link, so lets remove it.
                os.remove(latest_dir)
            os.symlink(self.dir, latest_dir, target_is_directory=True)

        if not ignore_git:
            exitcode = subprocess.call("git status", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if exitcode == 0:
                if not experimental:
                    d = subprocess.check_output(" [[ -z $(git status -s) ]] || echo 'dirty'", shell=True).decode()
                    if d.startswith("dirty"):
                        print(
                            "The current working directory is dirty, so can't store the git HEAD in the iteration directory.")
                        exit(1)

                    output = subprocess.check_output("git log --pretty=format:'%h' -n 1", shell=True).decode()
                    git_file = os.path.join(self.dir, "HEAD")
                    with open(git_file, "w") as git_file:
                        print(output, file=git_file)

        print(f'Using iteration directory [{self.dir}]')


def __collect_ec2_metadata(ip, ssh_user, ssh_options, dir):
    dest_dir = os.path.join(dir, ip)
    os.makedirs(dest_dir, exist_ok=True)

    ssh = SSH(ip, ssh_user, ssh_options)
    ssh.update()
    ssh.install("curl")
    ssh.exec("curl http://169.254.169.254/latest/dynamic/instance-identity/document > metadata.txt")
    ssh.scp_from_remote("metadata.txt", dest_dir)


def collect_ec2_metadata(ips, ssh_user, ssh_options, dir):
    run_parallel(__collect_ec2_metadata, [(ip, ssh_user, ssh_options, dir) for ip in ips])
