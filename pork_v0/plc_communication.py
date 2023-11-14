import pymcprotocol
import cv2
import numpy as np

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
if __name__=="__main__":
    # a=cv2.imread("./result/img_0.jpg")
    HOST="192.168.0.105"
    PORT=5001
    plc=plc_commu(HOST,PORT)
    plc.writebit("M1116",[0])
    # while True:
    #     cv2.imshow("show",a)
    #     key=cv2.waitKey(1)
    #     if key==ord("o"):
    #         plc.writebit("M1102",[1,1])
    #     elif key==ord("c"):
    #         plc.writebit("M1102",[0,0])
    #     elif key==ord("q"):
    #         break

print("ok!")