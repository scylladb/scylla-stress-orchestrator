from setuptools import setup, find_packages

setup(
    name='scyllaso',
    version='0.1.dev3',
    author='Peter Veentjer',
    author_email='peter.veentjer@scylladb.com',
    description='The Scylla Stress Orchestrator is Python 3 based framework for running various '
                'benchmark tools including cassandra-stress and scylla-bench.',
    long_description='The Scylla Stress Orchestrator is Python 3 based framework for running various '
                'benchmark tools including cassandra-stress and scylla-bench.',
    long_description_content_type='text/markdown',
    url='https://github.com/scylladb/scylla-stress-orchestrator',
    packages=find_packages(),
    python_requires='>=3.7',
    project_urls={
        'Bug Tracker': 'https://github.com/scylladb/scylla-stress-orchestrator/issues',
    },
    license_files=('LICENSE.txt',),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'make_key = scyllaso.bin.make_key:cli',
            'scylla_monitoring_start = scyllaso.bin.scylla_monitoring_start:cli',
            'scylla_monitoring_stop = scyllaso.bin.scylla_monitoring_stop:cli',
            'make_cpu_config = scyllaso.bin.make_cpu_config:cli',
            'kill_load_generators = scyllaso.bin.kill_load_generators:cli',
            'generate_benchmark = scyllaso.bin.generate_benchmark:cli',
            'flamegraph_cpu = scyllaso.bin.flamegraph_cpu:cli',
            'provision_terraform = scyllaso.bin.provision_terraform:provision',
            'unprovision_terraform = scyllaso.bin.provision_terraform:unprovision',
        ],
    }
)
