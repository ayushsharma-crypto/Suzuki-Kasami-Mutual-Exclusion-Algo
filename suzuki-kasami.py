import random
import threading
import numpy as np
from mpi4py import MPI
from collections import deque
from threading import Thread
from time import sleep
import sys
from datetime import datetime


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
total_nodes = comm.Get_size()

REQUEST_MESSAGE_TYPE = 'RN'
TOKEN_MESSAGE_TYPE = 'token'

LOCKS = {
    "request": threading.Lock(),
    "send": threading.Lock(),
    "release": threading.Lock(),
    "token": threading.Lock(),
    "cs": threading.Lock(),
    "rn": threading.Lock(),
}

DATA_STRUCTURE = {
    "token_queue": deque(),
    "LN": np.zeros(total_nodes),
    "RN": np.zeros(total_nodes),
    "has_token" : False,
    "in_cs": False,
    "waiting_for_token": False
}

def print_log(data):
    global rank
    # print(rank, data)
    filename = "Log1/process-"+str(rank)+".txt"
    # print(rank, filename)
    with open(filename, "a") as file:
        file.write(data)
        file.write("\n")

def listener():
    global DATA_STRUCTURE
    while True:
        mes = comm.recv(source=MPI.ANY_SOURCE)
        if mes[0] == REQUEST_MESSAGE_TYPE:
            with LOCKS["rn"]:
                rid = mes[1]
                seq = mes[2]
                DATA_STRUCTURE['RN'][rid] = max([seq, DATA_STRUCTURE['RN'][rid]])
                if DATA_STRUCTURE['RN'][rid] > seq:
                    print_log(
                        "%s: Request from %d has expired." % (datetime.now().strftime('%M:%S'), rid))
                    sys.stdout.flush()
                if DATA_STRUCTURE['has_token'] and \
                   not DATA_STRUCTURE['in_cs'] and \
                   DATA_STRUCTURE['RN'][rid] == DATA_STRUCTURE['LN'][rid]+1:
                   DATA_STRUCTURE['has_token'] = False
                   send_token(rid)
        elif mes[0] == TOKEN_MESSAGE_TYPE:
            with LOCKS['token']:
                print_log("%s: I'm %d and I got a token." % (datetime.now().strftime('%M:%S'), rank))
                sys.stdout.flush()
                DATA_STRUCTURE['has_token'] = True
                DATA_STRUCTURE['waiting_for_token'] = False
                DATA_STRUCTURE['LN'] = mes[1]
                DATA_STRUCTURE['token_queue'] = mes[2]
                run_cs()

def request():
    global DATA_STRUCTURE
    with LOCKS["request"]:
        if not DATA_STRUCTURE["has_token"]:
            DATA_STRUCTURE["RN"][rank] = DATA_STRUCTURE["RN"][rank] + 1
            print_log("%s: I'm %d and want a token for the %d time." % (datetime.now().strftime('%M:%S'), rank, DATA_STRUCTURE['RN'][rank]))
            sys.stdout.flush()
            DATA_STRUCTURE["waiting_for_token"]=True
            for i in range(total_nodes):
                if rank!=i:
                    comm.send([
                        REQUEST_MESSAGE_TYPE, 
                        rank, 
                        DATA_STRUCTURE["RN"][rank]
                    ], dest=i)

def send_token(recipient):
    global DATA_STRUCTURE
    with LOCKS["send"]:
        print_log("%s: I'm %d and sending the token to %d." % (datetime.now().strftime('%M:%S'), rank, recipient))
        sys.stdout.flush()
        comm.send([
            TOKEN_MESSAGE_TYPE, 
            DATA_STRUCTURE["LN"],
            DATA_STRUCTURE["token_queue"]
        ], dest=recipient)

def release_cs():
    global DATA_STRUCTURE
    with LOCKS["release"]:
        DATA_STRUCTURE["LN"][rank] = DATA_STRUCTURE["RN"][rank]
        for k in range(total_nodes):
            if k not in DATA_STRUCTURE["token_queue"]:
                if DATA_STRUCTURE["RN"][k]== (DATA_STRUCTURE["LN"][k]+1):
                    DATA_STRUCTURE["token_queue"].append(k)
                    print_log("%s: I'm %d and it adds %d to the queue. Queue after adding: %s." % (
                        datetime.now().strftime('%M:%S'), rank, k, str(DATA_STRUCTURE['token_queue'])))
                    sys.stdout.flush()
        if len(DATA_STRUCTURE["token_queue"])!=0:
            DATA_STRUCTURE["has_token"]=0
            send_token(DATA_STRUCTURE["token_queue"].popleft())

def run_cs():
    global DATA_STRUCTURE
    with LOCKS["cs"]:
        if DATA_STRUCTURE["has_token"]:
            DATA_STRUCTURE["in_cs"] = True
            print_log("%s: I am %d and execute %d CS." % (datetime.now().strftime('%M:%S'), rank, DATA_STRUCTURE['RN'][rank]))
            sys.stdout.flush()
            sleep(random.uniform(2, 5))
            DATA_STRUCTURE["in_cs"] = False
            print_log("%s: I'm %d and finished %d CS." % (datetime.now().strftime('%M:%S'), rank, DATA_STRUCTURE['RN'][rank]))
            sys.stdout.flush()
            release_cs()
            

if __name__=="__main__":
    DATA_STRUCTURE["RN"][0]=1
    # giving a token to start the process 0
    if rank==0:
        print_log("%s: I am %d and have a startup token." % (datetime.now().strftime('%M:%S'), rank))
        sys.stdout.flush()
        DATA_STRUCTURE["has_token"]=True
    
    try:
        listener_thread = Thread(target=listener)
        listener_thread.start()
    except:
        print_log("Error: unable to start thread!   ")
    
    while True:
        if not DATA_STRUCTURE["has_token"]:
            sleep(random.uniform(1,3));
            request()
        elif not DATA_STRUCTURE["in_cs"]:
            run_cs()
        while DATA_STRUCTURE["waiting_for_token"]:
            sleep(0.5)