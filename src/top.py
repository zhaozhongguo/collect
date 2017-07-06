# -*- coding: UTF-8 -*-
import os
import sys
import traceback
import commands
import time
import json
import datetime
import multiprocessing
from log import logging
import instance as collect_instance



OUTPUT_TOP_FILENAME = os.path.join(sys.path[0], "../output/top.json")


def get_top_cpu_info(cpu_line):
    """
    get cpu info from top cpu_line, eg:
        "%Cpu(s): 31.9 us, 33.3 sy,  0.0 ni, 20.8 id, 13.2 wa,  0.0 hi,  0.7 si,  0.0 st"
    """
    logging.debug("cpu_line:")
    logging.debug(cpu_line)
    
    cpu_dict = {}
    cpu_line = cpu_line.split(":")[1].split(",")
    for cpu_item in cpu_line:
        cpu_item = cpu_item.split(" ")
        cpu_key = cpu_value = None
        for item in cpu_item:
            if item:
                if not item.isalpha():
                    cpu_value = item
                else:
                    cpu_key = item
        if cpu_key and cpu_value:
            cpu_dict[cpu_key] = cpu_value
            
    logging.debug("cpu_dict:")
    logging.debug(cpu_dict)
    
    return cpu_dict



def get_top_mem_info(mem_line):
    """
    get mem info from top mem_line, eg:
        "KiB Mem :   488544 total,   433928 free,    12332 used,    42284 buff/cache"
    """
    logging.debug("mem_line:")
    logging.debug(mem_line)
    
    mem_dict = {}
    mem_line = mem_line.split(":")[1].split(",")
    for mem_item in mem_line:
        mem_item = mem_item.split(" ")
        mem_key = mem_value = None
        for item in mem_item:
            if item:
                if item.isdigit():
                    mem_value = item
                else:
                    mem_key = item
        if mem_key and mem_value:
            mem_dict[mem_key] = mem_value

    #calucate mem usage
    total = int(mem_dict['total'])
    free = int(mem_dict['free'])
    usage = str(round((total - free) * 100 / float(total), 1))
    mem_dict['usage'] = usage

    logging.debug("mem_dict:")
    logging.debug(mem_dict)
    
    return mem_dict


def get_top_info_by_instance(instance):
    """
    get top info by instance name.
    """
    top_time_begin = time.time()
    
    logging.debug("instance: ")
    logging.debug(instance[0])
    
    top_info = {}
    top_dict = instance[1]
    instance = instance[0]
    try:
        if instance['system'] == 'linux':
            #get top info
            (status, output) = commands.getstatusoutput(" ".join(["guestfish --ro -d", instance['name'], "-i command 'top -bn 1'"]))
            if status == 0:
                output = output.split("\n")
                cpu_line = output[2]
                cpu_dict = get_top_cpu_info(cpu_line)
                top_info['cpu'] = cpu_dict

                mem_line = output[3]
                mem_dict = get_top_mem_info(mem_line)
                top_info['mem'] = mem_dict

                top_dict[instance['uuid']] = top_info
            else:
                logging.error("Failed to get top info of " + str(instance))
        else:
            logging.debug("It's windows instance:%s, skip" % instance['uuid'])
    except Exception:
        logging.error(traceback.print_exc())
    
    logging.debug("top_info:")
    logging.debug(top_info)
    
    top_time_end = time.time()
    logging.info("instance: %s took: %d seconds." % (instance['name'], top_time_end - top_time_begin))
    return top_info


def get_all_top_info(max_process):
    """
    get all instances top info.
    """
    logging.debug("begin to collect system top info ...")
    
    try:
        if not os.path.exists(collect_instance.OUTPUT_INSTANCES_FILENAME):
            logging.warning("instances.json is not exist.")
            return {}
        else:
            all_instances = None
            with open(collect_instance.OUTPUT_INSTANCES_FILENAME, 'r') as f:
                all_instances = f.read()
            all_instances = json.loads(all_instances)

        top_dict = multiprocessing.Manager().dict()
        instance_list = all_instances
        instance_list = [(instance, top_dict) for instance in instance_list]
        pool = multiprocessing.Pool(max_process)
        ret = pool.map(get_top_info_by_instance, instance_list)
        pool.close()
        pool.join()

        top_dict = dict(top_dict)
    except Exception:
        logging.error(traceback.print_exc())
        return {}

    logging.debug("finished to collect system top info.")
    
    return top_dict


def save_top(max_process):
    top_info = get_all_top_info(max_process)
    top_info = json.dumps(top_info)
    with open(OUTPUT_TOP_FILENAME, 'w') as f:
        f.write(top_info)

        
if __name__ == '__main__':
    print datetime.datetime.now()
    save_top(16)
    print datetime.datetime.now()

