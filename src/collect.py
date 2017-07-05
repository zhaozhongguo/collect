# -*- coding: UTF-8 -*-
import multiprocessing
import datetime

import top
import instance
import stats


MAX_PROCESS_NUM = multiprocessing.cpu_count() / 2

if __name__ == '__main__':
    if MAX_PROCESS_NUM < 8:
        MAX_PROCESS_NUM = 8
    
    print datetime.datetime.now()
    stats.save_stats(MAX_PROCESS_NUM)
    print datetime.datetime.now()
    top.save_top(MAX_PROCESS_NUM)
    print datetime.datetime.now()
    instance.save_instances(MAX_PROCESS_NUM)
    print datetime.datetime.now()