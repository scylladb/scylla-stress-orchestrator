from time import sleep
from datetime import datetime, timedelta
import socket


def wait_for_port_start(node_ip, port, port_name, wait_reason='', timeout=900, connect_timeout=10,
                        max_tries_per_second=2):
    print(f'    [{node_ip}] Waiting for {port_name} port to start{wait_reason}. This could take a while.')

    backoff_interval = 1.0 / max_tries_per_second
    timeout_point = datetime.now() + timedelta(seconds=timeout)

    feedback_interval = 20
    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)

    while datetime.now() < timeout_point:
        # Make a probe connection.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(connect_timeout)
            try:
                sock.connect((node_ip, port))
            except:
                # There was a problem connecting to the port.
                sleep(backoff_interval)
                if datetime.now() > print_feedback_point:
                    print_feedback_point = datetime.now() + timedelta(seconds=feedback_interval)
                    print(f'    [{node_ip}] Still waiting for {port_name} port to start...')
            else:
                print(f'    [{node_ip}] Successfully connected to {port_name} port.')
                return

    raise Exception(f'Waiting for {port_name} to start timed out after {timeout} seconds for node: {node_ip}.')


def wait_for_cql_start(node_ip, timeout=900, connect_timeout=10, max_tries_per_second=2):
    wait_for_port_start(node_ip, 9042, 'CQL', ' (meaning node bootstrap finished)', timeout=timeout,
                        connect_timeout=connect_timeout, max_tries_per_second=max_tries_per_second)
