from time import sleep
from datetime import datetime, timedelta
import socket
from scyllaso.util import log_machine


def wait_for_cql_start(node_ip, timeout=7200, connect_timeout=10, max_tries_per_second=2):
    log_machine(node_ip, 'Waiting for CQL port to start (meaning node bootstrap finished). This could take a while.')

    backoff_interval = 1.0 / max_tries_per_second
    timeout_point = datetime.now() + timedelta(seconds=timeout)

    feedback_interval = 20
    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)

    while datetime.now() < timeout_point:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(connect_timeout)
            try:
                sock.connect((node_ip, 9042))
            except:
                # There was a problem connecting to CQL port.
                sleep(backoff_interval)
                if datetime.now() > print_feedback_point:
                    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)
                    log_machine(node_ip, 'Still waiting for CQL port to start...')

            else:
                log_machine(node_ip, 'Successfully connected to CQL port.')
                return

    raise Exception(f'Waiting for CQL to start timed out after {timeout} seconds for node: {node_ip}.')
