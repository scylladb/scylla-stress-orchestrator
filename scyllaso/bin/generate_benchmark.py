import os
import shutil
import getpass
import argparse
import pkg_resources
from scyllaso.bin import make_key


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("name",
                        help="The name of the benchmark.", nargs='?')
    parser.add_argument("--template",
                        help="The name of the benchmark template.", default="default")
    parser.add_argument("--resourceid",
                        help="An extra id to make resources unique. By default the username is used.")
    parser.add_argument("--list", help="List available benchmark templates", action='store_true')
    args = parser.parse_args()


    if args.list:
        print("default")
        print("cassandra4-scylla-comparison")
        return

    if not args.name:
        print("The name of the benchmark needs to be provided")
        exit(0)

    name = args.name
    if args.resourceid:
        resourceid = args.resourceid
    else:
        resourceid = getpass.getuser()

    cwd = os.getcwd()
    target_dir = os.path.join(cwd, name)

    if os.path.exists(target_dir):
        print(f"Can't generate benchmark: dir/file [{target_dir}] already exists")
        exit(1)

    copy_template(target_dir, args.template)

    os.chdir(target_dir)
    make_key.cli()
    process_templates(target_dir, resourceid)
    os.chdir(cwd)


def copy_template(target_dir, template):
    module_dir = os.path.dirname(pkg_resources.resource_filename('scyllaso', '__init__.py'))
    benchmarks_dir = os.path.join(module_dir, "benchmarks")
    template_dir = os.path.join(benchmarks_dir, template)
    if not os.path.exists(template_dir):
        print(f"Template directory [{template_dir}] does not exist.")
        exit(1)

    shutil.copytree(template_dir, target_dir)

    python_cache = os.path.join(target_dir, "__pycache__")
    if os.path.exists(python_cache):
        shutil.rmtree(python_cache)


def process_templates(target_dir, resourceid):
    for subdir, dirs, files in os.walk(target_dir):
        for filename in files:
            filepath = subdir + os.sep + filename
            if os.access(filepath, os.W_OK):
                f = open(filepath, 'r')
                old_text = f.read()
                f.close()

                new_text = old_text.replace("<resourceid>", resourceid)
                f = open(filepath, 'w')
                f.write(new_text)
                f.close()
