import time
import numpy as np
import pandas as pd
import pymcprotocol

CALIB1=[[  -0.007998  ,  0.91357   ,  0.01892 ],
[  -0.836571 ,  -0.018644,   -0.000386],
[   0.002375 ,   0.014936  ,  0.984037],
[ 124.95368  ,  32.680308, -179.073189]]
CALIB2=[[  -0.007998  ,  0.91357   ,  0.01892 ],
[  -0.836571 ,  -0.018644,   -0.000386],
[   0.002375 ,   0.014936  ,  0.984037],
[ 127.95368  ,  -30.680308, -170.073189]]
'''---- fanuc 통신----'''
from fanac_commu import fanuc_pos, POS, PROG_STAT, ALM
HOST = '192.168.0.223'
PORT = 502
POS1 = {'addr': 0, 'keys': POS.columns}
XYZ = POS.columns[0:6]
PR1 = {'addr': 50, 'keys': XYZ}
STAT1 = {'addr': 100, 'keys': PROG_STAT.columns}
ALM1 = {'addr': 150, 'keys': ALM.columns}


TRIG_CUSTOMXYZSLOW= {'addr': 350, 'values': np.array([1, 0, 0, 0, 0, 0, 0], np.int16)} #move to pr[1]   # R[131]
TRIG_CUSTOMXYZFAST= {'addr': 350, 'values': np.array([0, 1, 0, 0, 0, 0, 0], np.int16)}                  # R[132]
TRIG_CUSTOM1= {'addr': 350, 'values': np.array([0, 0, 1, 0, 0, 0, 0], np.int16)}    # Right_1           # R[133]
TRIG_CUSTOM2= {'addr': 350, 'values': np.array([0, 0, 0, 1, 0, 0, 0], np.int16)}    # Right_2           # R[134]
TRIG_CUSTOM3= {'addr': 350, 'values': np.array([0, 0, 0, 0, 1, 0, 0], np.int16)}    # Left_1            # R[135]
TRIG_CUSTOM4= {'addr': 350, 'values': np.array([0, 0, 0, 0, 0, 1, 0], np.int16)}    # Left_2            # R[136]
TRIG_ALL_RESET={'addr': 350, 'values': np.array([0, 0, 0, 0, 0, 0, 0], np.int16)}
TRIG_INITIAL = {'addr': 250, 'values': np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], np.int16)} #initialize register 
TRIG_PORKGRAB= {'addr': 250, 'values': np.array([0, 0, 0, 0, 1, 0, 0], np.int16)} # ROBOTio [4]             R[105]
TRIG_UPDOWN= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 1, 0], np.int16)} # ROBOTio [5]                 R[106]
TRIG_BASKETGRAB= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 1], np.int16)} # ROBOTio [6]             R[107]
TRIG_RIGHTUPDOWN= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0,], np.int16)} # ROBOTio [6]  R[108]
TRIG_RIGHTINOUT= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0], np.int16)} # ROBOTio [6]    R[109]
TRIG_RIGHTPULLPUSH= {'addr':250, 'values':np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1], np.int16)} # ROBOTio [6] R[110]
START_TRIG= {'addr': 300, 'values': np.array([0], np.int16)}  #R[151]
PLC_TRIG={'addr': 400, 'values': np.array([1], np.int16)}     #R[161]
'''----------------------------------------------------'''

'''----plc 통신----'''
from plc_communication import plc_commu
PLCHOST = '192.168.0.105'
PLCPORT = 5001
'''-------------------------------------'''
fanuc=fanuc_pos(HOST,PORT)
plc=plc_commu(PLCHOST,PLCPORT)
def IOcontrol(fanuc,START_TRIG,TRIG_INITIAL,plc,current_state,PLC_TRIG):
    while True:
        ROBOTio=fanuc.read_registers(TRIG_INITIAL,print_=False)
        if ROBOTio[4]!=current_state[4]:
            current_state[4]=ROBOTio[4]
            if ROBOTio[4]==1: # REG(105)
                plc.writebit("M1116",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[4]==0:
                plc.writebit("M1116",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[5]!=current_state[5]:
            current_state[5]=ROBOTio[5]
            if ROBOTio[5]==1: # REG(106)
                plc.writebit("M1115",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[5]==0:
                plc.writebit("M1115",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[6]!=current_state[6]:
            current_state[6]=ROBOTio[6]
            if ROBOTio[6]==1: # REG(107)
                plc.writebit("M1114",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[6]==0:
                plc.writebit("M1114",[0])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")

        if ROBOTio[7]!=current_state[7]:
            current_state[7]=ROBOTio[7]
            if ROBOTio[7]==1: # REG(108)
                plc.writebit("M1106",[0])
                plc.writebit("M1107",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[7]==0:
                plc.writebit("M1107",[0])
                plc.writebit("M1106",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")   

        if ROBOTio[8]!=current_state[8]:
            current_state[8]=ROBOTio[8]
            if ROBOTio[8]==1: # REG(107)
                plc.writebit("M1110",[0])
                plc.writebit("M1111",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[8]==0:
                plc.writebit("M1111",[0])
                plc.writebit("M1110",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")  

        if ROBOTio[9]!=current_state[9]:
            current_state[9]=ROBOTio[9]
            if ROBOTio[9]==1: # REG(107)
                plc.writebit("M1112",[0])
                plc.writebit("M1113",[1])
                fanuc.write_registers(PLC_TRIG)
            elif ROBOTio[9]==0:
                plc.writebit("M1113",[0])
                plc.writebit("M1112",[1])
                fanuc.write_registers(PLC_TRIG)
            else: print("error in IO")       
        if fanuc.check_finish(START_TRIG)==1:
            break

class plc_commu():
    def __init__(self,HOST,PORT):
        self.pymc3e = pymcprotocol.Type3E(plctype="iQ-L")
        self.pymc3e.setaccessopt(commtype="ascii")
        self.pymc3e.connect(HOST, PORT)
        print("connected")
    def readbit(self,name,size): 
        wordunits_values = self.pymc3e.batchread_bitunits(headdevice=name, readsize=size)
        # print(wordunits_values)
        return wordunits_values
    def writebit(self,name,value):
        self.pymc3e.batchwrite_bitunits(headdevice=name, values=value)

if __name__ == '__main__':
    plc.writebit('M1100',[0])
    plc.writebit('M1101',[1])
    plc.writebit('M1114',[1])
    plc.writebit('M1115',[0])
    plc.writebit('M1116',[1])
