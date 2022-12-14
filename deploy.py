import subprocess
import time
import os


class Deploy:
    def __init__(self):
        self.start_master_path = None
        self.start_worker_path = None
        self.executable_file_path = None
        self.stop_file_path = None
        self.master_client = None
        self.workers_clients = []

    def reserve_nodes(self, num_nodes, reservation_time):
        subprocess.check_output(f'preserve -# {num_nodes} -t 00:{reservation_time}:00', shell=True)
        status = subprocess.check_output("preserve -llist | grep ddps2201", shell=True).decode("utf-8").split()
        while status[6] != 'R':
            time.sleep(1)
            status = subprocess.check_output("preserve -llist | grep ddps2201", shell=True).decode("utf-8").split()

        node_list = status[8:]
        self.node_list = node_list

    def start_master(self):
        os.system(f'ssh {self.node_list[0]} python ~/ddps-assignment-2/master.py --host {self.node_list[0]} --port 9999 --task-name lfw_people')
    
    def start_worker(self):
        os.system(f'ssh {self.node_list[0]} python ~/ddps-assignment-2/worker.py --master-hostname {self.node_list[0]} --master-port 9999 --num-processes 5')

if __name__ == '__main__':
    deploy = Deploy()
    deploy.reserve_nodes(1, 15)
    deploy.start_master()
    deploy.start_worker()

