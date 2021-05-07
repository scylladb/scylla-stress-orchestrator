- targets:
%{ for ip in ips ~}
    - ${ip}:9100
%{ endfor ~}
  labels:
    cluster: ${cluster}
    dc: ${dc}

 
