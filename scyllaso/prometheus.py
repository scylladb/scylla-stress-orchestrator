from scyllaso.ssh import SSH
from scyllaso.util import log_important


def download(env, props, iteration):
    prometheus = Prometheus(env['prometheus_public_ip'][0],
                            props['prometheus_user'],
                            props['ssh_options'])
    prometheus.stop()
    prometheus.data_dir_download(iteration.dir)
    prometheus.start()


def download_and_clear(env, props, iteration):
    prometheus = Prometheus(env['prometheus_public_ip'][0],
                            props['prometheus_user'],
                            props['ssh_options'])
    prometheus.stop()
    prometheus.data_dir_download(iteration.dir)
    prometheus.data_dir_rm()
    prometheus.start()


class Prometheus:

    def __init__(self, ip, user, ssh_options, scylla_monitoring_version="3.8.2", scylla_version="4.4"):
        self.ip = ip
        self.user = user
        self.ssh_options = ssh_options
        self.scylla_monitoring_version = scylla_monitoring_version
        self.scylla_version = scylla_version

    def data_dir_upload(self, dir):
        log_important("Prometheus upload: started")
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.scp_to_remote(dir + "/*", "data")
        log_important("Prometheus upload: done")

    def stop(self):
        log_important("Prometheus stop: started")
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.exec(
            f"""
            cd scylla-monitoring-{self.scylla_monitoring_version}
            ./kill-all.sh
            """)
        log_important("Prometheus stop: done")

    def start(self):
        log_important("Prometheus start: started")
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.exec(
            f"""
            mkdir -p data
            cd scylla-monitoring-{self.scylla_monitoring_version}
            ./start-all.sh -v {self.scylla_version} -d ../data
            """)
        log_important("Prometheus start: done")

    def data_dir_download(self, dir):
        log_important("Prometheus download data: started")
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.scp_from_remote(f"data", dir)
        log_important("Prometheus download data: done")

    def data_dir_rm(self):
        log_important("Prometheus clear data: started")
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.exec("rm -fr data")
        log_important("Prometheus clear data: done")
