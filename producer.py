import redis, requests
import re, json, math
import time; from time import * 
import time as my_time
import requests; import re; import json; import logging
from datetime import datetime
import glv; from glv import Enabled
import settings
from functions import *
settings.init()

redis_server = redis.Redis(host='localhost', port=6379, db=0)

# Set the value of Enabled to Redis when the script starts
redis_server.set("Enabled", int(glv.Enabled))

queue_name = glv.queue_name
failed_tasks=glv.failed_tasks
completed_tasks=glv.completed_tasks
incompleted_tasks = glv.incompleted_tasks
switch_info_url = settings.switch_info_url
get_cmds_url = settings.url + "/getCommands"
update_req_url = settings.url + "/SetCommandStatus"
update_status_url= settings.url + "/postHealthMonitoring"


logger = logging.getLogger(__name__)
time_format = glv.time_format
logger.setLevel(logging.DEBUG)

try:
    from systemd.journal import JournaldLogHandler
    journald_handler = JournaldLogHandler()
    journald_handler.setFormatter(logging.Formatter(fmt=f'%(asctime)s - %(levelname)-8s - %(message)s', datefmt=time_format))
    logger.addHandler(APILogHandler(settings.mid_name))
except ImportError:
    logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s - %(levelname)-8s - %(message)s', datefmt=time_format)


def get_requests():
    commands = requests.post(get_cmds_url, headers={'Content-Type': 'application/json'}, auth=(settings.username, settings.password)).json()
    print (f"Got from commands from API: {commands['result']}")
    return commands['result']

def send_health_monitoring_update (mid_name, items_in_queue, items_in_process, items_failed, items_incomplete, Timestamp):
    try:
        payload = json.dumps(
            {
                "mid_name": mid_name,
                "items_in_queue": items_in_queue,
                "items_in_process": items_in_process,
                "items_failed": items_failed,
                "items_incomplete": items_incomplete,
                "timestamp": Timestamp
            })
        print(payload)
        answer = requests.post(update_status_url, data=payload,
                               headers={'Content-Type': 'application/json'}, auth=(settings.username, settings.password)).json()
    except Exception as e:
        logger.error('Error in send_health_monitoring_update: %s', str(e))

def cleanup_redis():
    # Cleanup failed tasks
    failed_count = redis_server.llen(failed_tasks)
    if failed_count > 0:
        logger.info("Cleaning up failed tasks...")
        for _ in range(failed_count):
            task = redis_server.lpop(failed_tasks)
            if task:
                redis_server.delete(task)

def redis_queue_push(task):
    record_id=task["record_id"]
    print(f"record_id: {record_id}")
    try:
            if bool(re.search('(active|failed)', task["dr_status"])):
                print(task["record_id"])
                job_status = redis_server.get(task["record_id"])
                print("job_status: ",job_status)
                print("recieved task:",task)

                if job_status is not None:
                    job_status=json.loads(job_status.decode())
                    #Completed task
                    #TODO Check competed
                    if "completed" in job_status["status"]:
                        print("completed")
                        output = re.sub("      ", "\n", job_status["output"])
                        send_status_update(task["record_id"], job_status["status"], output)
                        redis_server.rpush(completed_tasks, str(task))

                    #Active task
                    elif "active" in job_status["status"]:
                        print(f"Job status is {job_status} waiting to be executed")
                        redis_server.rpush(queue_name, str(task))

                    #failed task
                    if task["record_id"] not in [json.loads(t)["record_id"] for t in redis_server.lrange(failed_tasks,0,-1)]:
                        redis_server.rpush(failed_tasks, json.dumps(task))

                else:
                     #TODO when job is none?
                     print("else 11 {job_status}")
                     redis_server.rpush(queue_name, str(task))
                     print(f"else 12 {job_status}")
                     redis_server.set(record_id, "active")
                     print("else 13 {job_status}")
                     logger.info('Added %s to queue', task["record_id"])
                     print(f'added {task["record_id"]} to queue')

    except Exception as e:
        logger.error('Error in redis_queue_push: %s', str(e))

last_cleanup_time = None
if __name__ == "__main__":
    while True:
        enabled_value = redis_server.get("Enabled")
        if enabled_value and not bool(int(enabled_value.decode())):
            logger.info("Processing is disabled. Waiting for 'Enabled' to be True.")
            sleep(5)
            continue

        if last_cleanup_time is None or (datetime.now() - last_cleanup_time).seconds >= 3600:
            cleanup_redis()
            last_cleanup_time = datetime.now()

        tasks = get_requests()

        for task in tasks:
            if task['mid_name'] == settings.mid_server:
                record_id=task["record_id"]
                # Push task to the Redis queue
                redis_queue_push(task)

        tasks_for_mid_server = [task for task in tasks if task['mid_name'] == settings.mid_server]
        items_in_queue = len(tasks_for_mid_server)

        items_in_progress = sum(1 for task in tasks if task['dr_status'] == 'active')
        items_failed = redis_server.llen(failed_tasks)
        items_incomplete = redis_server.llen(incompleted_tasks)
        Timestamp = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')

        logger.info("%s, %s, %s, %s, %s, %s", settings.mid_server, items_in_queue, items_in_progress, items_failed, items_incomplete, Timestamp)        
        
        send_health_monitoring_update(settings.mid_server, items_in_queue, items_in_progress, items_failed, items_incomplete, Timestamp)
        sleep(10)