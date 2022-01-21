"python3 pyUDP_test.py -m rs -p 5555 -i 192.168.11.141:5555 --size 1000 --sleep 0.01 -l 100"
"python3 pyUDP_test.py -m c"
"9 999 999 999 packets maximum"

import asyncio
import logging
import argparse
import sys
import os
import time 
import struct

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file,mode='w')        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

# formatter = logging.Formatter('[%(asctime)s]: %(message)s')
# tx_logger = setup_logger('tx_log','UDPTX.log')
# rx_logger = setup_logger('rx_log','UDPRX.log')


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--mode',help='mode s(send),r(recieve),sr, sT',required=True)
    parser.add_argument('-p','--rport',help='recieving port ')
    parser.add_argument('-i','--ip',help='sending ip:port ')
    parser.add_argument('-s','--size',help='size of one message(min = 16) ', type=int)
    parser.add_argument('-t','--sleep',help='sleeptime between mesages')
    parser.add_argument('-l','--limit',help='packets limit')
    return parser


class RecieveDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, rtxtfile):
        self.rtxtfile = rtxtfile

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, RData, addr):
        pass
        # rx_logger.info("Recieved from %s:%s bytes %s"%(addr[0], addr[1], RData))
        with open('UDPRX.txt', 'a') as rtxtfile:
            self.rtxtfile.write(str(RData)+'\n')

    def close(self):
        if self.rtxtfile:
            self.rtxtfile.close()
            self.rtxtfile = None


class SenderDatagramProtocol(asyncio.DatagramProtocol):

    def __init__(self, addr, stxtfile):
        self.addr = addr
        self.stxtfile = stxtfile
        self.cnt = 0

    def connection_made(self, transport):
        self.transport = transport
        
    def sendto(self,SData):
        # tx_logger.info("Sent to %s:%s bytes %s"%(self.addr[0],self.addr[1], SData))
        self.stxtfile.write(str(SData)+'\n')
        self.transport.sendto(SData)
        print(self.cnt)
        self.cnt += 1

    def datagram_received(self, data, _):
        return 0

    def connection_lost(self, exc):
        return 0
    
    def close(self):
        if self.stxtfile:
            self.stxtfile.close()
            self.stxtfile = None

async def start_datagram_recieve(bind, port):
    # global protocolR
    global rtxtfile
    rtxtfile = open('UDPRX.txt', 'a')
    # with open('UDPRX.txt', 'a') as rtxtfile:
    loop = asyncio.get_running_loop()
    # return 
    transport, protocolR = await loop.create_datagram_endpoint(
        lambda: RecieveDatagramProtocol(rtxtfile), local_addr=(bind, port))


async def start_datagram_sender(size,sleep, limit, sending_host, sending_port, mode):
    CNT = 0
    global stxtfile
    stxtfile = open('UDPTX.txt', 'w')
    # with open('UDPTX.txt', 'a') as stxtfile:
    loop = asyncio.get_running_loop()
    protocolS = SenderDatagramProtocol((sending_host, sending_port), stxtfile)
    transport, protocolS = await loop.create_datagram_endpoint(
            lambda: protocolS, 
            remote_addr=(sending_host, sending_port))
            
    randB = os.urandom(1)

    while True:
        if CNT >= limit:

            # protocolS.close()
            # await asyncio.sleep(1)
            # global protocolR
            # protocolR.close()
            if 'r' in mode:
                global rtxtfile
                rtxtfile.close()
            stxtfile.close()
            # if 'r' in mode and 's' in mode:
            #     comparation()
            print('\x1b[1;32;40m' + 'Transmission completed, waiting for KeyboardInterrupt...' + '\x1b[0m')
            return 0
        if 'T' in mode:
            # cnt = 0
            # for i in f:
            #     if i == '0':
            #         cnt +=1
            #     else:
            #         print(cnt)
            #         cnt = 0
            # print(cnt)
            # exit()

            pack1 = int('180600800100E679',16)
            pack2 = int('1FF8',16)
            pack3 = int('01FF8000',16)
            pack4 = int('07FFFFFFFFFFFFFF',16)
            pack5 = int('FFFFFFFFFFFFFFFF',16)
            pack6 = int('FFFFFFE0',16)
            pack7 = int('07FE007FFFFFFE00',16)
            pack8 = int('7FFFFFFE007FE007',16)
            pack9 = int('FFFFFFE0',16)
            pack10 = int('03FF',16)
            pack11 = int('3FF0',16)
            pack12 = int('FFFFFFFFFFFFFFFF',16)
            pack13 = int('FFFFFFFFFFFFFFFF',16)
            pack14 = int('FFFFFC00',16)
            pack15 = int('FFC00FFFFFFFC00F',16)
            pack16 = int('FFFFFFC00FFC00FF',16)
            pack17 = int('FFFFFC00',16)
            pack18 = int('1FF8',16)
            pack19 = int('01FF8000',16)
            pack20 = int('07FFFFFFFFFFFFFF',16)
            pack21 = int('FFFFFFFFFFFFFFFF',16)
            pack22 = int('FFFFFFE0',16)
            pack23 = int('07FE007FFFFFFE00',16)
            pack24 = int('7FFFFFFE007FE007',16)
            pack25 = int('FFFFFFE0',16)


            SData = struct.pack('!Q1571xH10xI10xQQI10xQQI35xH11xH12xQQI10xQQI7xH10xI10xQQI10xQQI175x',
                    pack1,pack2,pack3,pack4,pack5,pack6,pack7,pack8,pack9,pack10,pack11,pack12,pack13,pack14,pack15,pack16,pack17,pack18,pack19,pack20,pack21,
                    pack22,pack23,pack24,pack25)
            CNT += 1
        else:
            ###Входные строки###
            tm = time.strftime("%H:%M:%S", time.localtime())
            head = f'N{CNT:010}T{tm}'
            CNT += 1
            
            lenInf = size - len(head)
            if (lenInf) <= 0:
                print('SIZE IS TOO SMALL!')
                return
            # SData = bytes(head,'utf-8')+os.urandom(lenInf)
            SData = bytes(head,'utf-8') + (randB*lenInf)
        await asyncio.sleep(sleep)
        protocolS.sendto(SData)
        # print(CNT)


def comparation():
    print('\x1b[1;33;40m' + 'Wait for comparation to finish' + '\x1b[0m')
    with open('UDPTX.txt', 'r') as tx_file, open('UDPRX.txt', 'r') as rx_file,  open('UDPRX.txt', 'r') as rx_file1:
        # difference = set(tx_file).symmetric_difference(rx_file)
        difference = set(tx_file).difference(rx_file)
        rx = rx_file1.readlines()
        incident = []
        for first in rx : 
            count = 0 
            for second in rx : 
                if first[3:13] == second[3:13] : 
                    count += 1 
                    incident.append(count)
        duplicates = set()
        index = 0
        while index < len(rx) :
            if incident[index] != 1 :
                duplicates.add(rx[index])
            index += 1
    
    difference = sorted(difference)
    with open('UDPDIFF.txt', 'a') as txtfile:
        for line in difference:
            txtfile.write(line)
        for line in duplicates:
            txtfile.write(f'd {line} \n')

def main(bind='0.0.0.0'):
    
    try:
        if os.path.exists('UDPDIFF.txt'):
            os.remove('UDPDIFF.txt')
        namespace = createParser().parse_args(sys.argv[1:])
        # namespace = createParser().parse_args(['-m', 'sT', '-i', '192.168.11.109:7764', '--size', '100', '--sleep', '0.1', '-l', '1000'])
        # namespace = createParser().parse_args(['-m', 'c'])     '-p', '7744',
        mode = namespace.mode

        loop = asyncio.get_event_loop()

        if mode == 'c':
            comparation()
        else:
            if os.path.exists('UDPRX.txt'):
                os.remove('UDPRX.txt')
            if os.path.exists('UDPTX.txt'):
                os.remove('UDPTX.txt')

            if 'r' in mode: 
                rport = namespace.rport
                transport = start_datagram_recieve(bind, rport)
                coro_rx = loop.create_task(transport)
                print('rmode')


            if 's' in mode:
                adr = namespace.ip.split(':')
                sending_host = adr[0]
                sending_port = adr[1]
                size = int(namespace.size) #bit
                sleep = float(namespace.sleep) #ms
                limit = int(namespace.limit)
                transport2 = start_datagram_sender(size, sleep,limit, sending_host, sending_port,mode)

                coro_tx = loop.create_task(transport2)
                print('smode')

        print('\x1b[2;32;40m' + 'Ctrl+C for exit.' + '\x1b[0m')


        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        global rtxtfile
        global stxtfile
        rtxtfile.close()
        stxtfile.close()
        print("Closing transport...")
        coro_rx.cancel()
        coro_tx.cancel()
        loop.close()
    except Exception as E:
        # logging.info(f'** Error {E} **')
        print(f'** Error {E} **')


if __name__ == '__main__':
    main()
