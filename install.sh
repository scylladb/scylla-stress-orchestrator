#!/bin/bash

set -e

python setup.py sdist
pip install --force-reinstall dist/scyllaso-0.1.dev3.tar.gz
echo "Install complete"