import os
from datetime import datetime
from sso.ssh import SSH
from sso.util import run_parallel
import uuid

class Prometheus:
    
    def __init__(self, ip, user, ssh_options):
        self.ip = ip
        self.user = user
        self.ssh_options = ssh_options

 
    # https://groups.google.com/g/prometheus-users/c/0ZkYVj_8X8Q    
    # https://www.robustperception.io/taking-snapshots-of-prometheus-data
    def take_snapshot(self, base_dir):
        ssh = SSH(self.ip, self.user, self.ssh_options)
        ssh.update()
        ssh.install("curl","jq")
        ssh.exec(
            f"""
            container_id=$(docker ps -q -f name=aprom)
            mkdir snapshots
            response=$(curl -XPOST http://localhost:9090/api/v2/admin/tsdb/snapshot)
            echo $response
            name=$(echo $response | jq -r '.name')
            docker cp ${{container_id}}:/prometheus/snapshots/${{name}}/ snapshots
            """)
        ssh.scp_from_remote(f"snapshots",base_dir)
        ssh.exec("rm -fr snapshots")
     
     
     
#     docker run --rm -p 9090:9090 -uroot -v /eng/snapshots/20210414T124945Z-380704bb7b4d7c03/:/prometheus prom/prometheus -config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus
