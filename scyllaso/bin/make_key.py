import subprocess
from os import path


def cli():
    if path.exists("key"):
        print("Key already found, skipping generation")
        return

    exitcode = subprocess.call(f"""ssh-keygen -P "" -m PEM -f key""", shell=True)
    if exitcode != 0:
        raise Exception(f'Failed to generate key')

    subprocess.call(f"""chmod 400 key""", shell=True)
    subprocess.call(f"""chmod 400 key""", shell=True)
