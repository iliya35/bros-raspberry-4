import paramiko
from pathlib import Path
import json
import logging
import asyncio
import ipaddress


def addres_plus_offset(address, offset):
    return (hex(int(address,16)+int(offset,16)))


class load_interface:
    count = 0
    def __init__(self):
        self.config_com = json
        if load_interface.count == 0:
            self.dload_ini('./configs/native_conf.ini')
        
    def dload_ini(self,filename):
        if Path(filename).is_file():
            with open(filename, "r") as read_file:
                try:
                    self.config_com = json.load(read_file)
                    logging.info(filename,'config readed')
                except Exception as E:
                    logging.info(f'{filename} not readed with err: {E} ')

            read_file.close()
        else:
            logging.info('error open file')


connection = []
hosts = []
native = load_interface()
dataFromEngine = asyncio.Queue()
linkStatus = False


def connect_to_host(host,user,pas):
    try :
        if host == 'is' and user == 'still' and pas == 'alive?':
            return client.get_transport().is_alive()
        if len(connection) > 0 :
            close()
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        client.connect(host, 
                username=user, 
                password=pas,auth_timeout=1)
        
        connection.append(client)
        hosts.append(host)
        logging.info(f'good connect to {host}')
        logging.info(f'good connect to {client.get_transport().is_alive()}')
        return True
    except Exception as E:
        logging.info(f'NO CONNECTION ERROR is {E}')
        return False
            

def close():
    for conn in connection:
        conn.close()
    connection.clear()


async def update (requestWithData):
    logging.info(f'cs.update: {requestWithData}')
    # print(f'cs.update: {requestWithData}')
    for req in requestWithData.values():
        request,data = req
        # logging.info(f'REQUEST {request}, DATA {data}')

        if request =='connect' :
            logging.info('# connect from update')
            connect_to_host(data['host'],data['user'],data['password'])
            continue
        if request == 'command':
            cmds =  native.config_com['Commands'][data]
            print('before write_dev_cmd(cmds)')
            await write_dev_cmd(cmds)           
            continue
        
        try:
            if len(request) != 0:
                await get_values(request,data)
            elif len(data) !=0 :
                await write_values(data)
            

        except Exception as E:
            logging.info(f'# {E}\n bad requests {request}')
    requestWithData = {}
    

async def ssh_alive():
    global linkStatus
    linkStatus = False
    for client in connection:
        linkStatus = client.get_transport().is_alive()
        

async def write_dev_cmd(data={}):
    commands = {}
    for dev,enum in data.items():
        sending_method = enum['sending_method']
        data = enum['data']
        for param, value in data.items():
            base_adress = native.config_com[dev]['base_adress']
            offset = native.config_com[dev]['params'][param]["offset"]
            adress = addres_plus_offset(base_adress,offset)
            sizeBit = native.config_com[dev]['params'][param]["sizeBit"]
            if sizeBit < 32:
                mode = native.config_com[dev]['mode']
                adress, value = await reg_formatcallback(dev,param,value)
                if adress == None and value == None:
                    print('Something gone wrong')
                    pass
            else:
                mode = 'manual'

            if 'hexip' in native.config_com[dev]['params'][param]:
                if native.config_com[dev]['params'][param]['hexip'] == 'True':
                    value = hex(int(ipaddress.IPv4Address(value)))

            command = make_write_command(dev = dev,key = param, mode = mode, adress = adress, value = value)
            commands[dev+"_"+param] = command
            if sending_method == 'individually':
                await send_to_device(commands)
                dict.clear(commands)
    if sending_method == 'individually':
        return 1
    else:
        await send_to_device(commands)
        return 1    


async def write_values(data={}):
    commands = {}
    command =''
    dev = ''
    key = ''
    # value_dev_c = {}
    for key, value in data.items():
        # logging.info(f' ключ {key}   значение {value}')
        try:
            fortry = int(key,16) #if it is hex adress in it continue
            mode = 'manual_hexadr'
        except: #if key is parameter it goes to except
            params = key.split('_')
            dev = params[0]
            key = params[1]
            # logging.info(f'# data_split {params}')  
            mode = native.config_com[dev]['mode']
            
        if mode == 'manual_hexadr':
            adress = key
            val = value
            command = make_write_command(dev, key, mode, adress, val)

        if mode == 'manual':
            adress = value[0]
            val = value[1]
            command = make_write_command(dev, key, mode, adress, val)

        if mode == 'reg':
            adress, new_val_hex = await reg_formatcallback(dev,key,value)
            if adress == None and new_val_hex == None:
                return command
            command = make_write_command(dev, key, mode, adress, new_val_hex)
            # logging.info(f'COMMAND {command}')
            
        if mode == 'shell':
            command = make_write_command(dev=dev, key=key, mode=mode, value=value)
        commands[dev+"_"+key] = command

    await send_to_device(commands)

# async def make_comand(dev,param_name,value):
#     mode = native.config_com[dev]['mode']
#     command =''

#     if mode == 'reg':
#         adress, new_val_hex = await reg_callbacknfrmt(dev,param_name,value)
#         if adress == None and new_val_hex == None:
#             return command
#         command = make_write_command(dev, param_name, mode, adress, new_val_hex)
#         logging.info(f'COMMAND {command}')
        

#     if mode == 'shell':
#         command = make_write_command(dev, param_name, mode,'', value)
        
    
#     if mode == 'manual':
#         adress = value[1][0]
#         val = value[1][1]
#         command = make_write_command(dev, param_name, mode, adress, val)
            
#     return command


async def reg_formatcallback(dev,param_name,value):
    
    param = native.config_com[dev]['params'][param_name]
    base_adress = native.config_com[dev]['base_adress']
    offset = param["offset"]
    adress = addres_plus_offset(base_adress,offset)
    size_bit =  param['sizeBit']
    if size_bit == 32:
        new_val_hex = hex(int(value,10))
        return adress, new_val_hex
    shift = 34 - param['shift'] - size_bit
    shift_size  =  shift + size_bit
    
    value_dev_cmd = {param_name:'devmem ' + adress}
    value_dev = await send_to_device(value_dev_cmd)
    if value_dev == {}:
        return None,None
    value_dev = format(int(value_dev[param_name],16),'#034b')

    try:
        if len(format(int(value),'b')) > size_bit: 
            logging.error('Слишком большое число')
            return None,None
    except: pass 
    
    try:
        if len(param['value_name']) > 0:
            value_cur = format(param['value'][param['value_name'].index(str(value))],'#0'+str(size_bit+2)+'b')
        else:
            value_cur =  format(int(value,0),'#0'+str(size_bit+2)+'b')
    except: 
        print(param['value_name'])
        print(str(value))
        print(param['value_name'].index(str(value)))
        print((param['value'][param['value_name'].index(str(value))]))

        logging.info('WRONG VALUE')
        print('WRONG VALUE')
        return None,None
    new_val = value_dev[:shift] + value_cur[2:] + value_dev[shift_size:]
    new_val_hex= hex(int(new_val,0))

    return adress, new_val_hex


async def get_values(request='',data={}):
    await asyncio.sleep(0.01)
    commands = {}
    # logging.info(f'#get_values request {request}')
    # logging.info(f'#get_values data {data}')
    base_adress = ''
    if request == 'man':
        base_adress = data['base_adr']
    dev = native.config_com[request]
    mode = dev['mode']
    if mode == 'shell':
        if len(data) == 0:
            await read_shell_region(request)
            return
        else:
            key = data['single']
            command = await make_read_command(request,key,mode)
            name = request + '_' + key
            
            commands[name] = command
            answer = await send_to_device(commands)
        dataFromEngine.put_nowait(answer_parsing(request,'',answer) ) 
        logging.info(f'# DATA is {dataFromEngine}')
        return
    if mode == 'CPU':
        command = await make_read_command(request,'',mode)
        commands['CPU_temp'] = command
        answer = await send_to_device(commands)
        raw = ((int(answer['CPU_temp']) * 503.975)/4096) - 273.15             
        raw = str(raw)[:4]             
        raw.replace('.',',')
        answer['CPU_temp'] = raw
                                                    ######################## Осталось доделать это и совместить с одиночным шеллом,
                                                    # а одиночный шелл в свою очережь можно соединить с регионом
        dataFromEngine.put_nowait(answer_parsing(request,'',answer) ) 
        logging.info(f'# DATA is {dataFromEngine}')
        return

    await read_device_region(request,base_adress)
    logging.info(f'# DATA is {dataFromEngine}')
    return


async def make_read_command(dev='',key='',mode=''):
    command = ''
    if mode == 'CPU':
        path = native.config_com[dev]['params']['temp']
        command = 'cat ' + path
        # answer = await send_to_device(command)
        # dataFromEngine.put_nowait(answer_parsing(dev_name,base_adress,answer_dict) )  
    elif mode == 'shell':
        path_driver = native.config_com[dev]['path_driver']
        command = 'cat '+ path_driver +'/'+ key.replace('-','_')
    return  command

def make_write_command(dev='', key='', mode='', adress='', value=''):
    command = ''
    if mode == 'reg' or mode == 'manual' or mode == 'manual_hexadr' or mode == 'test':
        command = 'devmem ' + adress + ' w ' + value
    elif mode == 'shell':
        path_driver = native.config_com[dev]['path_driver']
        command = 'echo -n ' + value + ' > ' + path_driver + '/' + key.replace('-','_')
    return command

async def read_shell_region(dev_name):
    commands = {}
    dev = native.config_com[dev_name]
    mode = dev['mode']
    params = dev['params']

    for key in params:
        command = await make_read_command(dev_name,key,mode)
        name = dev_name + '_' + key
        commands[name] = command
    answer_dict = await send_to_device(commands)
    dataFromEngine.put_nowait(answer_parsing(dev_name,'',answer_dict) )   
    return


async def read_device_region(dev_name,base_adress='',num=64):
    dev = native.config_com[dev_name]
    path_to_reg_read = '/opt/control/scripts/tools/region_read '
    if base_adress == '':
        base_adress =  dev['base_adress']
    command = path_to_reg_read + base_adress + f" {num}"  
    logging.info('read_device_region: '+command)

    for conn in connection:
        await asyncio.sleep(0.01)                             
        stdin, stdout, stderr = conn.exec_command(command)
        stdin.close()
        # print(dev_name)
        answer_dict = {}
        for line in stdout.read().splitlines():
            line = line.lower()
            line_separate = line.decode('utf-8').split(' - ')
            # print(line_separate)
            if len(line_separate) == 2:
                answer_dict[line_separate[0]] = line_separate[1]
    dataFromEngine.put_nowait(answer_parsing(dev_name,base_adress,answer_dict) )   
    return 1

def answer_parsing(dev_name, base_adress,answer_dict):
    # print(dev_name,answer_dict)
    par_answ = {}
    dev_params = native.config_com[dev_name]['params']
    mode = native.config_com[dev_name]['mode']
    # dev_base_addr =native.config_com[dev_name]['base_adress']
    if mode == 'shell' or mode == 'CPU':
        for key in dev_params.keys():
            # print(key)
            dev_key = dev_name+'_'+key
            if dev_key in answer_dict.keys():
                val = answer_dict[dev_key]
                # print(answer_dict[dev_key],val)
                par_answ[dev_key] = val
    else:
        dev_base_addr = base_adress
        for key,dev_param in dev_params.items():
        
            addr = addres_plus_offset(dev_base_addr,dev_param['offset'])
        
            if addr in  answer_dict:
                raw = answer_dict[addr]
                # print('dev_param',dev_param)
                # logging.info('dev_param',dev_param)
                if dev_name == 'man':
                    val = raw
                else:
                    val = extract_value(raw,dev_param)
                # print(answer_dict[addr],val)
                par_answ[dev_name+'_'+key] = val
    return par_answ


async def send_to_device(commands={}):
    answer = {}
    commands_str = ''
    for key, command in commands.items():
        commands_str += f'd=$({command}) && echo {key}=${{d}}\n'
    # logging.info(f'Send to device commands_str{commands_str}')
    for conn in connection:
        await asyncio.sleep(0.01)                              ###  Вызывает  WARNING коммуникатора !!!!!!!!!!!!!!!!!!!!!!!! 
        stdin, stdout, stderr = conn.exec_command(commands_str)
        stdin.close()
        for line in stdout.read().splitlines():
            line_separate = line.decode('utf-8').split('=')
            if len(line_separate) == 2:
                answer[line_separate[0]]=  line_separate[1]

    return answer
    


def extract_value(raw='',param={}):
        shift = param["shift"]
        sizebit = param["sizeBit"]
        # print('raw',raw)
        answer = int(("{0:>034b}".format(int(raw,16) >> shift))[-sizebit:],2)
        return answer


def from_word_to_bits(input=''):
    answer = str((input * 1)/1048576)[:5] + ' Мбит'
    return answer




# answer_dict = {'0x43c10000': '0x00000012', '0x43c10004': '0x05f5e100', '0x43c10008': '0x00000000', '0x43c1000c': '0x000000b4', '0x43c10010': '0x000000b4', '0x43c10014': '0x00001000', '0x43c10018': '0x00000000', '0x43c1001c': '0x00000000', '0x43c10020': '0x00000000', '0x43c10024': '0x00000000', '0x43c10028': '0x00001250', '0x43c1002c': '0x00000000', '0x43c10030': '0x00000000', '0x43c10034': '0x00000000', '0x43c10038': '0x0000124e', '0x43c1003c': '0x00000000'}
# par_ans = answer_parsing('stat1',answer_dict)
# print(par_ans)

# answer_dict = {'0x40010074': '0x00053020', '0x40010078': '0x00000006', '0x4001007c': '0x00000000', '0x40010080': '0x00000000', '0x40010084': '0x00000000', '0x40010088': '0x00000000', '0x4001008c': '0x00000000', '0x40010090': '0x00000000', '0x40010094': '0x00000000', '0x40010098': '0x00000000', '0x4001009c': '0x00000000', '0x400100a0': '0x000026ec', '0x400100a4': '0x00000000', '0x400100a8': '0x00000044', '0x400100ac': '0x00000000', '0x400100b0': '0x00004e5e'}
# par_ans = answer_parsing('modintStat',answer_dict)
# print(par_ans)