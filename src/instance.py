import time
import os
import sys
import json
import datetime
import multiprocessing
import commands
from log import logging

OUTPUT_INSTANCES_FILENAME = os.path.join(sys.path[0], "../output/instances.json")

def get_active_instance():
    """
    query all active instances
    """
    (status, output) = commands.getstatusoutput("virsh list | awk {'print $2'} | grep -v '^$'")
    if status == 0:
        output = output.split('\n')[1:]
        logging.debug("Active instances:")
        logging.debug(output)
        return output
    else:
        logging.error("Failed to query all active instances.")
        return []


def get_instance_info(instance):
    """
    query instance info
    """
    info = {}
    instance_list = instance[1]
    instance = instance[0]
    try:
        #query uuid
        (status, output) = commands.getstatusoutput(" ".join(["virsh dominfo ", instance, "| grep 'UUID' | awk '{print $2}'"]))
        if status == 0:
            info['name'] = instance
            info['uuid'] = output
        else:
            logging.error("Failed to query instance:%s uuid." % instance)
            return []
        
        #query operation system
        (status, output) = commands.getstatusoutput(" ".join(["virt-inspector -d", instance, "| grep '<name>linux</name>' | wc -l"]))
        if status == 0:
            if int(output) > 0:
                info['system'] = 'linux'
            else:
                info['system'] = 'windows'
        else:
            logging.error("Failed to query instance:%s operation system." % instance)
            return []
        logging.debug("instance info:")
        logging.debug(info)
        instance_list.append(info)
    except Exception:
        logging.error(traceback.print_exc())
    return info
        

def get_all_instance_info(max_process):
    """
    get all instances info.
    """
    logging.debug("begin to collect instance info ...")
    
    instance_list = multiprocessing.Manager().list()
    instances = get_active_instance()  
    instances = [(instance, instance_list) for instance in instances]
    pool = multiprocessing.Pool(max_process)
    ret = pool.map(get_instance_info, instances)
    pool.close()
    pool.join()

    instance_list = list(instance_list)

    logging.debug("finished to collect instance info.")
    
    return instance_list



def save_instances(max_process):
    all_inistances = get_all_instance_info(max_process)
    all_inistances = json.dumps(all_inistances)
    with open(OUTPUT_INSTANCES_FILENAME, 'w') as f:
        f.write(all_inistances)


if __name__ == '__main__':
    print datetime.datetime.now()
    save_instances(16)
    print datetime.datetime.now()