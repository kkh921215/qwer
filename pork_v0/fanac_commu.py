from pyModbusTCP.client import ModbusClient
import numpy as np
import pandas as pd
import time
POS_DATA = [[2, 2, 2, 2, 2, 2, 2, 2, 2,
    1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 2, 2,
    1, 1, 1, 1, 1, 1]]
POS_COL = ['X', 'Y', 'Z', 'W', 'P', 'R', 'E1', 'E2', 'E3', 
    'FLIP', 'LEFT', 'UP', 'FRONT', 'TURN4', 'TURN5', 'TURN6', 'VALIDC',
    'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 
    'VAILDJ', 'UF', 'UT', 'RESERVE1', 'RESERVE2', 'RESERVE3']
POS = pd.DataFrame(data=POS_DATA, columns=POS_COL)

ALM_DATA = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 40, 40, 9]]
ALM_COL = ['FC', 'AN', 'CC', 'CN', 'AS', 'YEAR', 'MON', 'DAY', 'HOUR', 'MIN', 'SEC', 'MSG', 'C_MSG', 'S_WORD']
ALM = pd.DataFrame(data=ALM_DATA, columns=ALM_COL)

PROG_STAT_DATA = [[8, 1, 1, 8]]
PROG_STAT_COL = ['NAME', 'LINE', 'STATUS', 'PARENT']
PROG_STAT = pd.DataFrame(data=PROG_STAT_DATA, columns=PROG_STAT_COL)

class fanuc_pos():
    def __init__(self, host, port):
        self.client = ModbusClient(host, port)        
    def read_pos(self, target):
        addr = target['addr']
        keys = target['keys']
        size = sum(POS.loc[0, keys])
        fdata = self.client.read_holding_registers(addr, size)
        if fdata:
            print('read success')
            df_pos = pd.DataFrame(columns=keys)
            idx = 0
            for ar, counts in zip(keys, POS.loc[0, keys]):
                if counts == 2:
                    # temp = np.array(fdata[idx:idx+counts], np.int16) # 이전 버전
                    temp = np.array(fdata[idx:idx+counts]).astype(np.int16) # numpy 버전 업데이트로 인해서 동작 방식이 바뀜에 따라 범위를 벗어나는 정수는 정수 배열로 변환이 허용되지 않는다 
                    temp.dtype = np.int32
                    df_pos.loc[0, ar] = temp[0]
                    idx += counts
                elif counts == 1:
                    temp = np.array(fdata[idx], np.int16)
                    df_pos.loc[0, ar] = temp
                    idx += counts

            print('read data: \n', df_pos)
            return df_pos

        else:
            print('read error')
            return None

    def read_alm(self, target):
        addr = target['addr']
        keys = target['keys']
        size = sum(ALM.loc[0, keys])
        fdata = self.client.read_holding_registers(addr, size)
        if fdata:
            print('read success')
            df_alarm = pd.DataFrame(columns=keys)
            idx = 0
            for ar, counts in zip(keys, ALM.loc[0, keys]):
                if counts > 2:
                    temp = b''
                    for c in range(counts):
                        temp += fdata[idx+c].to_bytes(2, byteorder='little')
                    df_alarm.loc[0, ar] = temp.decode('utf-8')
                    idx += counts
                elif counts == 1:
                    temp = np.array(fdata[idx], np.int16)
                    df_alarm.loc[0, ar] = temp
                    idx += counts

            print('read data: \n', df_alarm)
            return df_alarm

        else:
            print('read error')
            return None

    def read_stat(self, target):
        addr = target['addr']
        keys = target['keys']
        size = sum(PROG_STAT.loc[0, keys])
        fdata = self.client.read_holding_registers(addr, size)
        if fdata:
            print('read success')
            df_stat = pd.DataFrame(columns=keys)
            idx = 0
            for ar, counts in zip(keys, PROG_STAT.loc[0, keys]):
                if counts > 2:
                    temp = b''
                    for c in range(counts):
                        temp += fdata[idx+c].to_bytes(2, byteorder='little')
                    df_stat.loc[0, ar] = temp.decode('utf-8')
                    idx += counts
                elif counts == 1:
                    temp = np.array(fdata[idx], np.int16)
                    df_stat.loc[0, ar] = temp
                    idx += counts

            print('read data: \n', df_stat)
            return df_stat

        else:
            print('read error')

    def read_coils(self, target):
        addr = target['addr']
        values = target['values']
        size = len(values)
        coil_val = self.client.read_coils(addr, size)
        if coil_val:
            print('read success')
            print('read data: ', coil_val)
            return coil_val

        else:
            print('read error')

    def read_registers(self, target,print_=True):
        addr = target['addr']
        values = target['values']
        size = len(values)
        fdata = self.client.read_holding_registers(addr, size)
        if fdata:
            if print_==True:
                print('read success')
                print('read data: ', fdata)
            return fdata

        else:
            print('read error')

    def write_pr(self, target, df_pos):
        addr = target['addr']
        keys = target['keys']
        df_pr = pd.DataFrame(columns=keys)
        for ar, counts in zip(keys, POS.loc[0, keys]):
            if counts == 2:
                temp = np.zeros((1), dtype=np.int32)
                temp[0] = df_pos.loc[0, ar]
                temp.dtype = np.uint16
                df_pr.loc[0, ar] = temp
            elif counts == 1:
                temp = df_pos.loc[0, ar]
                df_pr.loc[0, ar] = temp
        pr = list()
        for d in df_pr.loc[0]:
            for s in range(d.size):
                pr.append(d[s])
        print('write data: ', pr)
        self.client.write_multiple_registers(addr, pr)

    def write_coils(self, target):
        addr = target['addr']
        values = target['values']
        print('write addr/data: ', addr, '/', values)
        self.client.write_multiple_coils(addr, values)

    def write_registers(self, target):
        addr = target['addr']
        values = target['values']
        print('write addr/data: ', addr, '/', values)
        self.client.write_multiple_registers(addr, values)

    def move_to(self, xyz, POSf ,PRf, TRIG):
        cur_pos = self.read_pos(POSf)
        pr1_pos = cur_pos
        pr1_pos.loc[0, 'X'] = np.int32(xyz[0])
        pr1_pos.loc[0, 'Y'] = np.int32(xyz[1])
        pr1_pos.loc[0, 'Z'] = np.int32(xyz[2])
        self.write_pr(PRf, pr1_pos)
        self.write_registers(TRIG)
    def move_by(self, xyz, POSf ,PRf, TRIG):
        cur_pos = self.read_pos(POSf)
        pr1_pos = cur_pos
        pr1_pos.loc[0, 'X'] = np.int32(cur_pos.loc[0, 'X']+xyz[0])
        pr1_pos.loc[0, 'Y'] = np.int32(cur_pos.loc[0, 'Y']+xyz[1])
        pr1_pos.loc[0, 'Z'] = np.int32(cur_pos.loc[0, 'Z']+xyz[2])
        self.write_pr(PRf, pr1_pos)
        self.write_registers(TRIG)
    def move_to_angle(self, xyzwpr, POSf ,PRf, TRIG):
        cur_pos = self.read_pos(POSf)
        pr1_pos = cur_pos
        pr1_pos.loc[0, 'X'] = np.int32(xyzwpr[0])
        pr1_pos.loc[0, 'Y'] = np.int32(xyzwpr[1])
        pr1_pos.loc[0, 'Z'] = np.int32(xyzwpr[2])
        pr1_pos.loc[0, 'W'] = np.int32(xyzwpr[3])
        pr1_pos.loc[0, 'P'] = np.int32(xyzwpr[4])
        pr1_pos.loc[0, 'R'] = np.int32(xyzwpr[5])

        self.write_pr(PRf, pr1_pos)
        self.write_registers(TRIG)

    def move_to_prog(self,TRIG,Current_IO):
        self.write_registers(Current_IO)
        self.write_registers(TRIG)

    def wait_for_finish(self,START_OFF):
        while True:
            start_signal=self.read_registers(START_OFF,print_=False)
            if start_signal==[1]:
                self.write_registers(START_OFF)
                print("move finish")
                break
        time.sleep(0.1)
    def check_finish(self,START_OFF):
        start_signal=self.read_registers(START_OFF,print_=False)
        if start_signal==[1]:
            self.write_registers(START_OFF)
            print("move finish")
            return 1
        else: return -1      
if __name__ == '__main__':
    HOST = '192.168.0.223'
    PORT = 502

    POS1 = {'addr': 0, 'keys': POS.columns}
    XYZ = POS.columns[0:6]
    PR1 = {'addr': 50, 'keys': XYZ}
    STAT1 = {'addr': 100, 'keys': PROG_STAT.columns}
    ALM1 = {'addr': 150, 'keys': ALM.columns}
    TRIG1 = {'addr': 250, 'values': np.array([1, 0, 1, 0, 1, 1, 1,0,0,0], np.int16)}
    TRIG2 = {'addr': 300, 'values': np.array([0], np.int16)}
    TRIG2 = {'addr': 300, 'values': np.array([0], np.int16)}
    PORK_NUM={'addr': 380, 'values': np.array([2], np.int16)}
    TRIG_INITIAL = {'addr': 250, 'values': np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], np.int16)} #initialize register 
    TRIG_ALL_RESET={'addr': 350, 'values': np.array([1, 1, 1, 1, 1, 1, 1], np.int16)}
    START_TRIG= {'addr': 300, 'values': np.array([0], np.int16)} 
    crx10 = fanuc_pos(HOST, PORT)
    crx10.write_registers(TRIG_INITIAL)
    crx10.write_registers(TRIG_ALL_RESET)
   
    # a=crx10.read_registers(TRIG1)
    # print(a)
    # pr1_pos = cur_pos
    # pr1_pos.loc[0, 'X'] = np.int32(4)
    # pr1_pos.loc[0, 'Y'] = np.int32(5)
    # pr1_pos.loc[0, 'Z'] = np.int32(9)

    # crx10.write_pr(PR1, pr1_pos)
    # pr1_pos = crx10.read_pos(PR1)

    # stat1 = crx10.read_stat(STAT1)
    # alm1 = crx10.read_alm(ALM1)

    # crx10.write_registers(TRIG2)
    # trig1 = crx10.read_registers(TRIG2)
    