import pymcprotocol
import time

# PLC command
COMM1 = 'open'
COMM2 = 'close'
COMM3 = 'up'
COMM4 = 'down'
COMM5 = 'release'
COMM6 = 'hold'
COMM7 = 'grip'
COMM8 = 'ungrip'

class plc_slmp:
    def __init__(self, config, idx):
        self.config = config['plc']
        self.delay = self.config['delay']

        if self.config['plc_type'] == 'iQ-F':
            self.pymc3e = pymcprotocol.Type3E(plctype="iQ-L")

        if self.config['data_code'] == 'Binary':
            pass
        elif self.config['data_code'] == 'ascii':
            self.pymc3e.setaccessopt(commtype="ascii")

        plc_ip = self.config['plc_host']
        plc_port = self.config['plc_port'][idx]

        self.pymc3e.connect(plc_ip, plc_port)
        print("PLC connect complete")
        # servo initializing
        if idx == 0:
            self.servo_pos('init')

    def bit_read(self, headdevice, readsize):
        bitunits_values = self.pymc3e.batchread_bitunits(headdevice=headdevice, readsize=readsize)

        return bitunits_values

    def bit_write(self, headdevice, values):
        self.pymc3e.batchwrite_bitunits(headdevice=headdevice, values=values)

    def close(self):
        self.pymc3e.close

    def M_IO(self, comm):
        start_point = self.config['command'][comm][0]
        w_data = self.config['command'][comm][1]
        self.bit_write(start_point, w_data)
        time.sleep(self.delay)

    def servo_pos(self, line):
        line_data = self.config['servo'][line]
        if line == 'init':
            servo_state = [True]
        else:
            servo_state = [False]
        if self.bit_read(line_data[1], 1) == servo_state:
            print('Servo is moving')
            self.M_IO(COMM4)
            time.sleep(self.delay)
            self.bit_write(line_data[0], [1])
            time.sleep(self.delay)
            self.bit_write(line_data[0], [0])
            while self.bit_read(line_data[1], 1) == servo_state:
                time.sleep(self.delay)
            print('Servo move done')
            if line != 'init':
                self.M_IO(COMM3)
                time.sleep(self.delay)