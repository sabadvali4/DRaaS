import redis, requests
import re, json
import time; from time import * 
import requests; import re; import json; import logging

redis_server = redis.Redis()
queue_name = "api_req_queue"
snow_url = "https://bynetprod.service-now.com/api/bdml/switch"
switch_info_url = snow_url + "/getSwitchLogin"
get_cmds_url = snow_url + "/getCommands"
update_req_url = snow_url + "/SetCommandStatus"
update_status_url= snow_url + "/postHealthMonitoring"
mid_server = "Linux_Mid_Server"  ##hard coded name of mid server

# get an instance of the logger object this module will use
logger = logging.getLogger(__name__)

# Check if the systemd.journal module is available
try:
    from systemd.journal import JournaldLogHandler

    # instantiate the JournaldLogHandler to hook into systemd
    journald_handler = JournaldLogHandler()

    # set a formatter to include the level name
    journald_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

    # add the journald handler to the current logger
    logger.addHandler(journald_handler)

except ImportError:
    # systemd.journal module is not available, use a different logging mechanism
    logging.basicConfig(level=logging.DEBUG)

# Optionally set the logging level
logger.setLevel(logging.DEBUG)


def get_requests():
    commands = requests.post(get_cmds_url, headers={'Content-Type': 'application/json'}, auth=('admin', 'Danut24680')).json()
    #print (commands['result'])
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
                               headers={'Content-Type': 'application/json'}, auth=('admin', 'Danut24680')).json()

    except Exception as e:
        logger.error('Error in send_status_update: %s', str(e))


def send_health_monitoring_update(mid_name, items_in_queue, items_in_process, timestamp):
    try:
        payload = json.dumps(
            {
                "mid_name": mid_name,
                "items_in_queue": items_in_queue,
                "items_in_process": items_in_process,
                "timestamp": timestamp
            })
        print(payload)
        answer = requests.post(update_status_url, data=payload,
                               headers={'Content-Type': 'application/json'}, auth=('admin', 'Danut24680')).json()

    except Exception as e:
        logger.error('Error in send_health_monitoring_update: %s', str(e))


def redis_queue_push(TASKS):
    try:
        for TASK in TASKS:
            if bool(re.search('(active|failed)', TASK["dr_status"])):
                kv_status = redis_server.get(TASK["record_id"])
                if kv_status is not None:
                    kv_status = json.loads(kv_status.decode())
                    if "completed" in kv_status["status"]:
                        output = re.sub("      ", "\n", kv_status["output"])
                        send_status_update(TASK["record_id"], kv_status["status"], output)

                    else:
                        # Check if mid_name matches the specified value
                        if TASK.get("mid_name", "") == mid_server:
                            redis_server.rpush(queue_name, str(TASK))
                            logger.info('Added %s to queue', TASK["record_id"])
                            print(f'added {TASK["record_id"]} to queue')
                        else:
                            logger.info('Skipped %s because mid_name does not match', TASK["record_id"])
                else:
                    # Check if mid_name matches the specified value
                    if TASK.get("mid_name", "") == mid_server:
                        redis_server.rpush(queue_name, str(TASK))
                        logger.info('Added %s to queue', TASK["record_id"])
                        print(f'added {TASK["record_id"]} to queue')
                    else:
                        logger.info('Skipped %s because mid_name does not match', TASK["record_id"])

    except Exception as e:
        logger.error('Error in redis_queue_push: %s', str(e))


if __name__ == "__main__":
    while True:
        tasks_len = len(get_requests())  # Use a different variable name
        redis_queue_push(get_requests())
        timestamp = time()
        send_health_monitoring_update(mid_server, redis_server.llen(queue_name), (tasks_len - redis_server.llen(queue_name)), timestamp)
        sleep(10)
