import os
import shutil
import getpass
import argparse
import pkg_resources
from scyllaso.bin import make_key


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="The name of the benchmark.")
    args = parser.parse_args()

    dir_name = args.name
    cwd = os.getcwd()
    target_dir = os.path.join(cwd, dir_name)

    if os.path.exists(target_dir):
        print(f"Can't generate benchmark: dir/file [{target_dir}] already exists")
        exit(1)

    copy_template(target_dir)

    os.chdir(target_dir)
    make_key.cli()
    process_templates(target_dir)
    os.chdir(cwd)


def copy_template(target_dir):
    module_dir = os.path.dirname(pkg_resources.resource_filename('scyllaso', '__init__.py'))
    template_dir = os.path.join(module_dir, "template")
    shutil.copytree(template_dir, target_dir)

    python_cache = os.path.join(target_dir, "__pycache__")
    if os.path.exists(python_cache):
        shutil.rmtree(python_cache)


def process_templates(target_dir):
    username = getpass.getuser()
    for subdir, dirs, files in os.walk(target_dir):
        for filename in files:
            filepath = subdir + os.sep + filename
            if os.access(filepath, os.W_OK):
                f = open(filepath, 'r')
                old_text = f.read()
                f.close()

                new_text = old_text.replace("<name>", username)
                f = open(filepath, 'w')
                f.write(new_text)
                f.close()
