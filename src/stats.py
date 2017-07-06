# -*- coding: UTF-8 -*-
import os
import sys
import traceback
import commands
import time
import re
import json
import datetime
import multiprocessing
from log import logging
import instance as collect_instance



OUTPUT_STATS_FILENAME = os.path.join(sys.path[0], "../output/stats.json")


def get_dommemstat_usage(instance):
    logging.debug("instance:")
    logging.debug(instance)
    percent = None
    query = ' '.join(["virsh dommemstat", instance['name'], "| grep 'available\|unused'"])
    (status, info) = commands.getstatusoutput(query)
    if status == 0:
        info = info.split('\n')
        logging.debug("dommemstat:" + str(info))
        unused = available = None
        for item in info:
            if item.find('unused') != -1:
                unused = int(item.split(' ')[1])
            elif item.find('available') != -1:
                available = int(item.split(' ')[1])
            else:
                logging.debug("Unknow info: %s." % info)
        logging.debug("unused:" + str(unused))
        logging.debug("available:" + str(available))
        if unused and available:
            percent = str(round(float(available - unused) * 100 / available, 1))
    else:
        logging.error("Failed to query dommemstat for instance:%s" % instance['name'])
    logging.debug("mem_percent:" + percent)
    return percent



def get_domstats(instance):
    domstats = {}
    
    query = ' '.join(["virsh domstats", instance['name']])
    (status, output) = commands.getstatusoutput(query)
    if status == 0:
        output = output.split("\n")
        cpu_dict = {}

        net_dict = {}
        net_receive = {}
        net_send = {}

        disk_dict = {}
        disk_ops_read = {}
        disk_ops_write = {}
        disk_octet_write = {}
        disk_octet_read = {}
        for item in output:
            if item:
                item = item.replace(' ', '').split("=")
                key = item[0]
                if key == 'cpu.time':
                    cpu_dict[key] = item[1]
                elif key == 'vcpu.current':
                    cpu_dict[key] = item[1]
                elif re.match(r'net\.\d+\.rx\.bytes', key, flags=0):
                    net_receive[key] = item[1]
                elif re.match(r'net\.\d+\.tx\.bytes', key, flags=0):
                    net_send[key] = item[1]
                elif re.match(r'block\.\d+\.rd\.reqs', key, flags=0):
                    disk_ops_read[key] = item[1]
                elif re.match(r'block\.\d+\.rd\.bytes', key, flags=0):
                    disk_octet_read[key] = item[1]
                elif re.match(r'block\.\d+\.wr\.reqs', key, flags=0):
                    disk_ops_write[key] = item[1]
                elif re.match(r'block\.\d+\.wr\.bytes', key, flags=0):
                    disk_octet_write[key] = item[1]

        net_dict['net_receive'] = net_receive
        net_dict['net_send'] = net_send

        disk_dict['disk_ops_read'] = disk_ops_read
        disk_dict['disk_ops_write'] = disk_ops_write
        disk_dict['disk_octet_write'] = disk_octet_write
        disk_dict['disk_octet_read'] = disk_octet_read

        domstats['cpu_dict'] = cpu_dict
        domstats['net_dict'] = net_dict
        domstats['disk_dict'] = disk_dict
    else:
        logging.error("Failed to query dommemstat for instance:%s" % instance['name'])
    logging.debug("domstats:")
    logging.debug(str(domstats))
    return domstats
    
    


def get_instance_stats(instance):
    """
    get dom stats by instance name.
    """
    stats_time_begin = time.time()
    
    logging.debug("instance: ")
    logging.debug(instance[0])
    
    stats_info = {}
    stats_dict = instance[1]
    instance = instance[0]

    domstats_begin = get_domstats(instance)
    time_begin = time.time()
    time.sleep(5)
    domstats_end = get_domstats(instance)
    time_end = time.time()
    
    #cpu 
    try:
        cpu_percent = str(round((int(domstats_end['cpu_dict']['cpu.time']) - int(domstats_begin['cpu_dict']['cpu.time'])) / float(time_end - time_begin) / 10000000 / int(domstats_end['cpu_dict']['vcpu.current']), 1))
        if cpu_percent > 100:
            cpu_percent = 100
        stats_info['cpu_percent'] = cpu_percent
    except Exception:
        logging.error(traceback.print_exc())
   
    #net
    try:
        receive_end = 0
        for item in domstats_end['net_dict']['net_receive'].values():
            receive_end += int(item)
        receive_begin = 0
        for item in domstats_begin['net_dict']['net_receive'].values():
            receive_begin += int(item)
        net_receive_traffic = (receive_end - receive_begin) / float(time_end - time_begin)
        stats_info['net_receive_traffic'] = str(round(net_receive_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    try:
        send_end = 0
        for item in domstats_end['net_dict']['net_send'].values():
            send_end += int(item)
        send_begin = 0
        for item in domstats_begin['net_dict']['net_send'].values():
            send_begin += int(item)
        net_send_traffic = (send_end - send_begin) / float(time_end - time_begin)
        stats_info['net_send_traffic'] = str(round(net_send_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    #disk
    try:
        disk_ops_read_end = 0
        for item in domstats_end['disk_dict']['disk_ops_read'].values():
            disk_ops_read_end += int(item)
        disk_ops_read_begin = 0
        for item in domstats_begin['disk_dict']['disk_ops_read'].values():
            disk_ops_read_begin += int(item)
        disk_ops_read_traffic = (disk_ops_read_end - disk_ops_read_end) / float(time_end - time_begin)
        stats_info['disk_ops_read_traffic'] = str(round(disk_ops_read_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    try:
        disk_ops_write_end = 0
        for item in domstats_end['disk_dict']['disk_ops_write'].values():
            disk_ops_write_end += int(item)
        disk_ops_write_begin = 0
        for item in domstats_begin['disk_dict']['disk_ops_write'].values():
            disk_ops_write_begin += int(item)
        disk_ops_write_traffic = (disk_ops_write_end - disk_ops_write_end) / float(time_end - time_begin)
        stats_info['disk_ops_write_traffic'] = str(round(disk_ops_write_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    try:
        disk_octet_read_end = 0
        for item in domstats_end['disk_dict']['disk_octet_read'].values():
            disk_octet_read_end += int(item)
        disk_octet_read_begin = 0
        for item in domstats_begin['disk_dict']['disk_octet_read'].values():
            disk_octet_read_begin += int(item)
        disk_octet_read_traffic = (disk_octet_read_end - disk_octet_read_end) / float(time_end - time_begin)
        stats_info['disk_octet_read_traffic'] = str(round(disk_octet_read_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    try:
        disk_octet_write_end = 0
        for item in domstats_end['disk_dict']['disk_octet_write'].values():
            disk_octet_write_end += int(item)
        disk_octet_write_begin = 0
        for item in domstats_begin['disk_dict']['disk_octet_write'].values():
            disk_octet_write_begin += int(item)
        disk_octet_write_traffic = (disk_octet_write_end - disk_octet_write_end) / float(time_end - time_begin)
        stats_info['disk_octet_write_traffic'] = str(round(disk_octet_write_traffic, 1))
    except Exception:
        logging.error(traceback.print_exc())
        
    try:
        mem_percent = get_dommemstat_usage(instance)
        stats_info['mem_percent'] = mem_percent
    except Exception:
        logging.error(traceback.print_exc())
    
    stats_dict[instance['uuid']] = stats_info
    
    logging.debug("stats_info:")
    logging.debug(stats_info)
    
    stats_time_end = time.time()
    logging.info("instance: %s takes: %d seconds." % (instance['name'], stats_time_end - stats_time_begin))
    return stats_info


    
def get_all_instance_stats(max_process):
    """
    get all instances stats info.
    """
    logging.debug("begin to collect dom stats info ...")
    
    try:
        if not os.path.exists(collect_instance.OUTPUT_INSTANCES_FILENAME):
            logging.warning("instances.json is not exist.")
            return {}
        else:
            all_instances = None
            with open(collect_instance.OUTPUT_INSTANCES_FILENAME, 'r') as f:
                all_instances = f.read()
            all_instances = json.loads(all_instances)
        
        stats_dict = multiprocessing.Manager().dict()
        instance_list = all_instances
        instance_list = [(instance, stats_dict) for instance in instance_list]
        pool = multiprocessing.Pool(max_process)
        ret = pool.map(get_instance_stats, instance_list)
        pool.close()
        pool.join()

        stats_dict = dict(stats_dict)
    except Exception:
        logging.error(traceback.print_exc())
        return {}

    logging.debug("finished to collect dom stats info.")
    
    return stats_dict

def save_stats(max_process):
    stats_info = get_all_instance_stats(max_process)
    stats_info = json.dumps(stats_info)
    with open(OUTPUT_STATS_FILENAME, 'w') as f:
        f.write(stats_info)
        

if __name__ == '__main__':
    print datetime.datetime.now()
    save_stats(16)
    print datetime.datetime.now()
