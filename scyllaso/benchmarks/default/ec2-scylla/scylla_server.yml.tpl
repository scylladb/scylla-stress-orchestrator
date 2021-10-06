- targets:
%{ for ip in ips ~}
    - ${ip}
%{ endfor ~}
  labels:
    cluster: ${cluster}
    dc: ${dc}

 
