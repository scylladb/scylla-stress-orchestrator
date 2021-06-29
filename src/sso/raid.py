from sso.ssh import PSSH

class RAID:
    def __init__(self, ips, ssh_user, device_name_wildcard, raid_device_name, properties, raid_level=0, filesystem='xfs'):
        self.ips = ips
        self.ssh_user = ssh_user
        self.device_name_wildcard = device_name_wildcard
        self.raid_device_name = raid_device_name
        self.properties = properties
        self.raid_level = raid_level
        self.filesystem = filesystem

    def install(self):
        joined_ips = ','.join(self.ips)
        print(f'    [{joined_ips}] raid: starting creating RAID')
        pssh = PSSH(self.ips, self.ssh_user, self.properties['ssh_options'])
        pssh.install('mdadm')
        pssh.exec(f"""
            if [[ ! -b /dev/md/{self.raid_device_name} ]]; then
                sudo mdadm --create --verbose /dev/md/{self.raid_device_name} --level={self.raid_level} \
                    --force --raid-devices=$(ls {self.device_name_wildcard} | wc -l) {self.device_name_wildcard}
                
                # '/dev/md/name' maps to '/dev/md[0-9]+'
                MD_NAME=$(basename $(readlink /dev/md/{self.raid_device_name}))

                # Tuning (as in https://www.scylladb.com/2018/07/06/scylla-vs-cassandra-ec2/)
                sudo sh -c "echo 1 > /sys/block/$MD_NAME/queue/nomerges"
                sudo sh -c "echo 8 > /sys/block/$MD_NAME/queue/read_ahead_kb"

                sudo mkfs.{self.filesystem} -f /dev/$MD_NAME
                mkdir {self.raid_device_name}
                sudo mount /dev/$MD_NAME {self.raid_device_name}
                sudo chown $(id -u) {self.raid_device_name}
            fi
        """)
        print(f'    [{joined_ips}] raid: finished creating RAID')
