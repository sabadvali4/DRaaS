import redis, requests
import re, json
from time import sleep
import logging
from systemd.journal import JournaldLogHandler

# get an instance of the logger object this module will use
logger = logging.getLogger(__name__)
# instantiate the JournaldLogHandler to hook into systemd
journald_handler = JournaldLogHandler()
# set a formatter to include the level name
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(message)s'))
# add the journald handler to the current logger
logger.addHandler(journald_handler)
# optionally set the logging level
logger.setLevel(logging.DEBUG)

redis_server = redis.Redis()
queue_name = "api_req_queue"
snow_url = "https://bynetprod.service-now.com/api/bdml/switch"
switch_info_url = snow_url+"/getSwitchLogin"
get_cmds_url = snow_url+"/getCommands"
update_req_url = snow_url+"/SetCommandStatus"

def get_requests():
    commands = requests.post(get_cmds_url, headers={'Content-Type': 'application/json'}, auth=('admin','Danut24680')).json()
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
        #print(payload)
        answer = requests.post(update_req_url, data=payload, 
                    headers={'Content-Type': 'application/json'}, auth=('admin','Danut24680')).json()
        
    except Exception as e:
        logger.error('Error in send_status_update: %s', str(e))

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
                        redis_server.rpush(queue_name, str(TASK))
                        logger.info('Added %s to queue', TASK["record_id"])
                        print(f'added {TASK["record_id"]} to queue')
                else:
                    redis_server.rpush(queue_name, str(TASK))
                    logger.info('Added %s to queue', TASK["record_id"])
                    print(f'added {TASK["record_id"]} to queue')

    except Exception as e:
        logger.error('Error in redis_queue_push: %s', str(e))

if __name__ == "__main__":
    while True:
        redis_queue_push(get_requests())
        sleep(10)
    

