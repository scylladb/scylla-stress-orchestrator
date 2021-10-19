from scyllaso.ssh import PSSH
from scyllaso.util import log


class RAID:
    def __init__(self, public_ips, user, device_name_wildcard, raid_device_name, level, properties):
        self.level = level
        self.public_ips = public_ips
        self.user = user
        self.device_name_wildcard = device_name_wildcard
        self.raid_device_name = raid_device_name
        self.properties = properties

    def install(self):
        ips = ','.join(self.public_ips)
        log(f'[{ips}] raid: starting creating RAID')
        pssh = PSSH(self.public_ips, self.user, self.properties['ssh_options'])
        pssh.exec(f"""
            if [[ ! -b /dev/md/{self.raid_device_name} ]]; then
                sudo mdadm --create --verbose /dev/md/{self.raid_device_name} --chunk=256 --metadata=1.2 --level={self.level} --force --raid-devices=$(ls {self.device_name_wildcard} | wc -l) {self.device_name_wildcard}
                
                # /dev/md/raid_device_name maps to /dev/md[0-9]+
                MD_NAME=$(basename $(readlink /dev/md/{self.raid_device_name}))

                # Tuning
                sudo sh -c "echo 1 > /sys/block/$MD_NAME/queue/nomerges"
                sudo sh -c "echo 8 > /sys/block/$MD_NAME/queue/read_ahead_kb"
                sudo sh -c "echo none > /sys/block/$MD_NAME/queue/scheduler"

                sudo mkfs.xfs -f /dev/$MD_NAME
                mkdir {self.raid_device_name}
                sudo mount /dev/$MD_NAME {self.raid_device_name}
                sudo chown $(id -u) {self.raid_device_name}
            fi
        """)
        log(f'[{ips}] raid: finished creating RAID')
