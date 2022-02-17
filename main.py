import subprocess
import requests
import time
import schedule
import datetime

farmers_config = []

with open('config.txt', 'r') as z:
    for line in z:
        line = line.strip()
        if 'chia dir:' in line:
            chia_dir = line.strip('chia dir: ')
        if 'Slack URL: ' in line:
            slack_url = line.strip('Slack URL: ')
        if 'schedule update: ' in line:
            scd_update = line.strip('schedule update: ')
        if 'schedule check : ' in line:
            scd_check = line.strip('schedule check : ')
        if 'plots:' in line:
            plots_config = line.strip('plots: ')
        if 'Remote Harvester for IP:' in line:
            farmers_config.append(line)


def check_farm():
    farmers_recorded = []
    run_once = 0

    with open('summary.txt', 'r') as z:
        for line in z:
            line = line.strip()
            if 'Connection error' in line:
                notification = ["Connection Error Check Main Farmer"]
                update_pause = True
                return notification, update_pause
            if 'Farming status: Farming' in line:
                notification = [line]
            if 'Remote Harvester for IP:' in line:
                farmers_recorded.append(line)
            if 'Farming status: Not available' in line:
                notification = [line]
                update_pause = True
                return notification, update_pause
            if 'Farming status: Not synced or not connected to peers' in line:
                notification = [line]
                update_pause = True
                return notification, update_pause
            if 'Plot count for all harvesters:' in line:
                plots_recorded = line.strip('Plot count for all harvesters:')
                notification.append(line)

    if plots_config == plots_recorded:
        update_pause = False
        return notification, update_pause

    for x in farmers_config:
        if x not in farmers_recorded:
            if run_once == 0:
                notification.append("Missing Harvester: ")
                run_once = 1
            y = x.strip("Remote Harvester for IP: ")
            notification.append(y)
    if plots_config > plots_recorded:
        xx = (int(plots_config) - int(plots_recorded))
        xx = "Missing: %s Plots" % xx
        notification.append(xx)
        update_pause = True
        return notification, update_pause


def slack_send(payload):
    response = requests.post('%s' % slack_url, data=payload)
    print(response.text)


def Get_farm_status(d_update):
    with open('summary.txt', 'w') as z:
        Farm_state = subprocess.run(".\chia farm summary", cwd=r'%s' % chia_dir, shell=True, stdout=z, text=True)

    if Farm_state.returncode > 0:
        payload = '{"text":" Error cant get Farm Summary"}'
        slack_send(payload)
        day = datetime.date.today()
        daytime = datetime.datetime.now()
        log = open("Logs\log File - " "%s" ".txt" % day, 'a')
        log.write("\n" + "%s " % day + daytime.strftime("%H:%M:%S") + "\n")
        log.write("-----------------------Error cant get Farm summary----------------------------------------------" + "\n")
        log.write("-----------------------Error cant get Farm summary----------------------------------------------" + "\n")
        log.close()

    if Farm_state.returncode == 0:
        notification, update_pause = check_farm()
        if update_pause == True or d_update == True:
            payload = '\\n'.join(notification)
            payload = '{"text":"%s"}' % payload
            slack_send(payload)
        Log_update()


def Log_update():
    day = datetime.date.today()
    daytime = datetime.datetime.now()
    log = open("Logs\log File - " "%s" ".txt" % day, 'a')
    log.write("\n" + "%s " % day + daytime.strftime("%H:%M:%S") + "\n")
    with open('summary.txt', 'r') as z:
        for line in z:
            line = line.strip()
            log.write(line + "\n" )
    log.close()


def check():
    d_update = False
    print("Check")
    Get_farm_status(d_update)


def update():
    d_update = True
    print("update")
    Get_farm_status(d_update)


update()
schedule.every(int(scd_check)).minutes.do(check)
schedule.every(int(scd_update)).minutes.do(update)

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Press Ctrl-C to terminate while statement")
    pass