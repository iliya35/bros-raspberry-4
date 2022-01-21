import logging
logging.basicConfig(handlers=[logging.FileHandler(filename="data_cmdfw.log", encoding='utf-8', mode='w')], level=logging.INFO)
import sys
import csv
import time
import asyncio
import argparse
import commandsender as cs



def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', required=True)
    parser.add_argument('-c', '--cmd')
    parser.add_argument('-t')
    parser.add_argument('-s')

    # parser.add_argument ('-u', '--username', default='root')
    # parser.add_argument ('-p', '--password', default='root')
    return parser


loop = asyncio.new_event_loop()
loop.set_debug(False)
asyncio.set_event_loop(loop)

queueRequest = asyncio.Queue()

async def communicator():
    requestFromGuiQueue = {}
    logging.info('communicator begin')
    print('communicator begin')
    while True:
        await asyncio.sleep(0.1)
        if not queueRequest.empty():
            logging.info(f'queueRequest({queueRequest.qsize()}):{queueRequest}')
            qs = queueRequest.qsize()
            for i in range(1, qs+1):
                requestFromGuiQueue[i] = queueRequest.get_nowait()
            await cs.update(requestFromGuiQueue)
            requestFromGuiQueue.clear()
        
async def connect(host):
    logging.info('Connecting...')
    print('Connecting...')
    queueRequest.put_nowait(('connect',{ 
                'host':host,
                'user':'root',
                'password':'root'}))


async def send_cmds(host='192.168.11.109', cmd = ''):
    if cmd != '':
        logging.info(f'Sending {cmd}')
        print(f'Sending {cmd}')
        queueRequest.put_nowait(('command',cmd))

async def request_dev(devices, timer):
    while(True):
        for dev in devices:
            queueRequest.put_nowait((dev,{}))
        await asyncio.sleep(timer)

async def read_dev(devices, timer):
    timeCSVname = host+time.strftime("_%m%d_%H:%M:%S", time.localtime())
    with open(f'reports/{timeCSVname}.csv', 'w', newline='') as csvfile:
        fieldnames= []
        for dev in devices:
            for name in cs.native.config_com[dev]['params'].keys():
                fieldnames.append(dev+"_"+name)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        C = 1

        while(True):
            dataEng = {}
            while not cs.dataFromEngine.empty():
                data = cs.dataFromEngine.get_nowait()
                # print(data)
                dataEng.update(data)
                if cs.dataFromEngine.empty():
                    writer.writerow(dataEng)

            print('█' * C)
            C += 1
            if C > 100:
                C = 1
            await asyncio.sleep(timer)        

namespace = createParser().parse_args(sys.argv[1:])
# namespace = createParser().parse_args(['-i', '192.168.11.113', '-c','obzor_eth3_tx'])#,'-t','1',]) 

host = namespace.ip
cmd = namespace.cmd
timer = namespace.t
statistic = namespace.s

log_devices = ['stat1','stat3','modintStat']



try:

    cmd_snd=loop.create_task(communicator())
    conn = loop.create_task(connect(host))

    if cmd == None:
        logging.info('NO COMMAND')
        print('\nNO COMMAND\n')
    elif not cmd in cs.native.config_com['Commands'].keys():
        logging.error('NON-EXISTENT COMMAND')
        print('\n ERROR: NO COMMAND OR NON-EXISTENT COMMAND\n')
    else:
        cmd_user=loop.create_task(send_cmds(host,cmd))

    if statistic != None:
        if timer == None:
            timer = 1
        timer = float(timer)

        req_dev = loop.create_task(request_dev(log_devices, timer))
        r_dev = loop.create_task(read_dev(log_devices, timer))

    
    # lnk = loop.create_task(linkStatus(host))
    
    loop.run_forever()
except KeyboardInterrupt:
    canceltasks = [task.cancel() for task in asyncio.all_tasks()]
    logging.info(f"cancelling {len(canceltasks)} tasks")
finally:
    logging.info("closing loop")
    loop.close()
print('end')





