"""Setup
Usage:
    setup.py <network_size> <ip_file> <pem_file> [options]

Options:
    -h, --help      Print help message and exit
    -m, --max INT   Set the max number of servers per instance [default: 5]
    -s, --server    make server configs [default: False]
    -b, --bench     make benchmakr configs [default: False]
    -c, --chaos     make chaos config [default: False]
"""

from docopt import docopt
from os import path
import json
import paramiko
import time

RAFT_PATH = "/home/ec2-user/go-workplace/src/github.com/kpister/raft"

# rm cfgs/*
# scp -r cfg_* user@ip:~/go/src/github.com/kpister/raft/server/

if __name__ == '__main__':
    args = docopt(__doc__)
    
    servers = int(args['<network_size>'])
    max_size = int(args['--max'])

    make_server_configs = args['--server']
    make_benchmark_config = args['--bench']
    make_chaos_config = args['--chaos']

    if servers < 1:
        raise Exception("Network size cannot be less than 1")

    if max_size < 1:
        raise Exception("Max size cannot be less than 1")

    if not path.exists(args['<ip_file>']):
        raise Exception("IP file does not exist")

    if not path.exists(args['<pem_file>']):
        raise Exception(".pem file does not exist")

    ips = []

    for line in open(args['<ip_file>']):
        ips.append(line.strip())

    if len(ips) * max_size < servers:
        raise Exception(f"Too many servers requested, can only host {len(ips) * max_size}")

    ip_dict = {} # store list of ips and config files needed, for config file transfer
    addrs = [] # store a list of all the ip address with ports, for config files

    idx = 0
    for i in range(servers):
        ip = ips[i//max_size]
        if ip not in ip_dict:
            ip_dict[ip] = []

        addrs.append(f'{ip}:{8000 + (i % max_size)}')
        ip_dict[ip].append(idx)
        idx += 1

    cfg = {
            "ServersAddr": addrs, 
            "FollowerMax": 7000, 
            "FollowerMin": 2000, 
            "HeartbeatTimeout": 30
            }

    if make_server_configs:
        pem = paramiko.RSAKey.from_private_key_file(args['<pem_file>'])
        for ip in ip_dict.keys():
            # connect to server
            print(f'Connecting to {ip}')
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username="ec2-user", pkey=pem)

            # clear cfgs folder
            cmd = f"rm -f {RAFT_PATH}/server/cfgs/*"
            print(f'Executing: {cmd}')
            client.exec_command(cmd)

            cmd = f"mkdir {RAFT_PATH}/server/cfgs/"
            print(f'Executing: {cmd}')
            client.exec_command(cmd)

            cmd = f"pkill server"
            client.exec_command(cmd)

            cmd = f"cd {RAFT_PATH}/server ; go install"
            client.exec_command(cmd)

            cmd = f"sh /home/ec2-user/removefiles"
            client.exec_command(cmd)

            for sid in ip_dict[ip]:
                cfg["ID"] = sid
                # copy in needed cfgs
                cmd = f"echo '{json.dumps(cfg)}' > {RAFT_PATH}/server/cfgs/cfg{sid}.json"
                print(f'Executing: {cmd}')
                client.exec_command(cmd)

            cmd = "/home/ec2-user/start.sh\n"

            transport = client.get_transport()
            channel = transport.open_session()
            pty = channel.get_pty()
            shell = client.invoke_shell()
            shell.send(cmd)
            time.sleep(10)
            shell.close()
            channel.close()

            client.close()

    if make_benchmark_config:
        # make a config file for the benchmark 
        bench_cfg = {
                "ServersAddr": addrs, 
                "NumClients": 10,
                "NumConns": 1,
                "Duration": 10,
                "ValSize": 5,
                "NumEntries": 5,
                "KeySize": 5,
                "NumRequests": 1000,
                "Operation": "PUT"
                }
        bench_json = json.dumps(bench_cfg)
        benchmark_path = "/Users/admin/go-workplace/src/github.com/kpister/raft/benchmark"
        bench_cfg_file = open(benchmark_path + "/benchmark.json", "w")
        bench_cfg_file.write(bench_json)

    if make_chaos_config:
        chaos_config = {
                "ServersAddr": addrs
                }
        chaos_json = json.dumps(chaos_config)
        chaos_path = "/Users/admin/go-workplace/src/github.com/kpister/raft/chaosClient"
        chaos_config_file = open(benchmark_path + "/chaosConfig.json", "w")
        chaos_config_file.write(chaos_json)