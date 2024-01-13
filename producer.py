import redis, requests
import re, json, math
import time; from time import * 
import time as my_time
import requests; import re; import json; import logging
from datetime import datetime
import glv; from glv import Enabled
import settings
settings.init()

redis_server = redis.Redis(host='localhost', port=6379, db=0)

# Set the value of Enabled to Redis when the script starts
redis_server.set("Enabled", int(glv.Enabled))

queue_name = "api_req_queue"
switch_info_url = settings.switch_info_url
get_cmds_url = settings.url + "/getCommands"
update_req_url = settings.url + "/SetCommandStatus"
update_status_url= settings.url + "/postHealthMonitoring"

# this module will be used to get an instance of the logger object 
logger = logging.getLogger(__name__)
# Define the time format
time_format = "%Y-%m-%d %H:%M:%S"
# Optionally set the logging level
logger.setLevel(logging.DEBUG)
try:
    from systemd.journal import JournaldLogHandler

    # Instantiate the JournaldLogHandler to hook into systemd
    journald_handler = JournaldLogHandler()

    journald_handler.setFormatter(logging.Formatter(fmt=f'%(asctime)s - %(levelname)-8s - %(message)s', datefmt=time_format))

    # Add the journald handler to the current logger
    logger.addHandler(journald_handler)

except ImportError:
    # systemd.journal module is not available, use basic console logging
    logging.basicConfig(level=logging.DEBUG, format=f'%(asctime)s - %(levelname)-8s - %(message)s', datefmt=time_format)

def get_requests():
    commands = requests.post(get_cmds_url, headers={'Content-Type': 'application/json'}, auth=(settings.username, settings.password)).json()
    print (f"Got from commands from API: {commands['result']}")
    return commands['result']


def send_status_update(ID, STATUS, OUTPUT):
    try:
        payload = json.dumps(
            {
                "command_id": f"{ID}",
                "command_status": f"{STATUS}",
                "command_output": f"{OUTPUT}"
            })
        # print(payload)
        answer = requests.post(update_req_url, data=payload,
                               headers={'Content-Type': 'application/json'}, auth=(settings.username, settings.password)).json()

    except Exception as e:
        logger.error('Error in send_status_update: %s', str(e))


def send_health_monitoring_update (mid_name, items_in_queue, items_in_process, items_failed,Timestamp):
    try:
        payload = json.dumps(
            {
                "mid_name": mid_name,
                "items_in_queue": items_in_queue,
                "items_in_process": items_in_process,
                "items_failed": items_failed,
                "timestamp": Timestamp
            })
        print(payload)
        answer = requests.post(update_status_url, data=payload,
                               headers={'Content-Type': 'application/json'}, auth=(settings.username, settings.password)).json()

    except Exception as e:
        logger.error('Error in send_health_monitoring_update: %s', str(e))


def redis_queue_push(task):
    record_id=task["record_id"]
    print(f"record_id: {record_id}")
    try:
            if bool(re.search('(active|failed)', task["dr_status"])):
                job_status = redis_server.get(task["record_id"]).decode()
                print(job_status)
                print("recieved task:",task)

                if job_status is not None:
                    if "completed" in job_status:
                        print("completed")
                  
                        output = re.sub("      ", "\n", job_status)
                        print("completed1")
                        send_status_update(task["record_id"], job_status, output)
                    elif "active" in job_status:
                        print(f"Job status is {job_status} waiting to be executed")
                else:
                     print("else 11 {job_status}")
                     redis_server.rpush(queue_name, str(task))
                     print(f"else 12 {job_status}")
                     redis_server.set(record_id, "active")
                     print("else 13 {job_status}")
                     logger.info('Added %s to queue', task["record_id"])
                     print(f'added {task["record_id"]} to queue')

    except Exception as e:
        logger.error('Error in redis_queue_push: %s', str(e))

if __name__ == "__main__":
    while True:
        # Get the value of 'Enabled' from Redis
        enabled_value = redis_server.get("Enabled")

        # If 'Enabled' is False, skip processing tasks
        if enabled_value and not bool(int(enabled_value.decode())):
            logger.info("Processing is disabled. Waiting for 'Enabled' to be True.")
            sleep(5)
            continue

        # Get the tasks from the API
        tasks = get_requests()
        for task in tasks:
            if task['mid_name'] == settings.mid_server:
                record_id=task["record_id"]
                # Push task to the Redis queue
                redis_queue_push(task)


        items_in_progress = sum(1 for task in tasks if task['dr_status'] == 'active')
        items_failed = sum(1 for task in tasks if task['dr_status'] == 'failed')
        # Format timestamp as HH:MM:SS
        Timestamp = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')
        print(f"{settings.mid_server}, {len(tasks)} , {items_in_progress}, {items_failed} ,{Timestamp}")
        # send_health_monitoring_update(settings.mid_server, len(tasks) , items_in_progress, items_failed ,Timestamp)
        
        #### redis_queue_push(tasks)
        # Sleep for 10 seconds before the next iteration
        sleep(10)
