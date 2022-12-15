import subprocess
import time
import os
import random


class Deploy:
    def __init__(self, save_path):
        self.start_master_path = None
        self.start_worker_path = None
        self.executable_file_path = None
        self.stop_file_path = None
        self.master_client = None
        self.workers_clients = []
        self.master_port = f'99{random.randint(0, 99)}'
        self.save_path = save_path

    def reserve_nodes(self, num_nodes, reservation_time):
        os.system('scancel -u ddps2201')
        time.sleep(10)
        subprocess.check_output(f'preserve -# {num_nodes} -t 00:{reservation_time}:30', shell=True)
        status = subprocess.check_output("preserve -llist | grep ddps2201", shell=True).decode("utf-8").split()
        while status[6] != 'R':
            time.sleep(1)
            status = subprocess.check_output("preserve -llist | grep ddps2201", shell=True).decode("utf-8").split()

        node_list = status[8:]
        self.node_list = node_list

    def start_master(self):
        os.system(f'ssh {self.node_list[0]} python ~/ddps-assignment-2/master.py --host {self.node_list[0]} --port {self.master_port} --task-name digits --save-path {self.save_path} &')
    
    def start_worker(self):
        for node in self.node_list:
            os.system(f'ssh {node} python ~/ddps-assignment-2/worker.py --master-hostname {node} --master-port {self.master_port} --num-processes 5 &')

if __name__ == '__main__':
    for i in range(4):
        for j in range(20):
            deploy = Deploy(f'~/ddps-assignment-2/results/digits_{i+1}/experiment_{j}')
            deploy.reserve_nodes(i + 1, 3)
            deploy.start_master()
            deploy.start_worker()
            time.sleep(60 * 3.6)

