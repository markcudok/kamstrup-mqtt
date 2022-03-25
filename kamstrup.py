from __future__ import print_function
from paho.mqtt import client as mqtt
import serial
import math
import sys
import datetime
import urllib
import urllib.request

# MQTT
broker = 'BROKERSIPADDRESS'
port = 1883
client_id = 'kamstrup-meter'
username = 'YOURMQTTUSERNAME'
password = 'YOURMQTTPASSWORD'
client = mqtt.Client(client_id)
client.username_pw_set(username, password)
client.connect(broker, port)

# Kamstrup
kamstrup_402_var = {                # Decimal Number in Command
 0x003C: "Heat Energy (E1)",        #60
 0x0050: "Power",                   #80
 0x0056: "Temp1",                   #86
 0x0057: "Temp2",                   #87
 0x0059: "Tempdiff",                #89
 0x004A: "Flow",                    #74
 0x0044: "Volume",                  #68
 0x008D: "MinFlow_M",               #141
 0x008B: "MaxFlow_M",               #139
 0x008C: "MinFlowDate_M",           #140
 0x008A: "MaxFlowDate_M",           #138
 0x0091: "MinPower_M",              #145
 0x008F: "MaxPower_M",              #143
 0x0095: "AvgTemp1_M",              #149
 0x0096: "AvgTemp2_M",              #150
 0x0090: "MinPowerDate_M",          #144
 0x008E: "MaxPowerDate_M",          #142
 0x007E: "MinFlow_Y",               #126
 0x007C: "MaxFlow_Y",               #124
 0x007D: "MinFlowDate_Y",           #125
 0x007B: "MaxFlowDate_Y",           #123
 0x0082: "MinPower_Y",              #130
 0x0080: "MaxPower_Y",              #128
 0x0092: "AvgTemp1_Y",              #146
 0x0093: "AvgTemp2_Y",              #147
 0x0081: "MinPowerDate_Y",          #129
 0x007F: "MaxPowerDate_Y",          #127
 0x0061: "Temp1xm3",                #97
 0x006E: "Temp2xm3",                #110
 0x0071: "Infoevent",               #113
 0x03EC: "HourCounter",             #1004
}

units = {
    0: '', 1: 'Wh', 2: 'kWh', 3: 'MWh', 4: 'GWh', 5: 'j', 6: 'kj', 7: 'Mj',
    8: 'Gj', 9: 'Cal', 10: 'kCal', 11: 'Mcal', 12: 'Gcal', 13: 'varh',
    14: 'kvarh', 15: 'Mvarh', 16: 'Gvarh', 17: 'VAh', 18: 'kVAh',
    19: 'MVAh', 20: 'GVAh', 21: 'kW', 22: 'kW', 23: 'MW', 24: 'GW',
    25: 'kvar', 26: 'kvar', 27: 'Mvar', 28: 'Gvar', 29: 'VA', 30: 'kVA',
    31: 'MVA', 32: 'GVA', 33: 'V', 34: 'A', 35: 'kV',36: 'kA', 37: 'C',
    38: 'K', 39: 'l', 40: 'm3', 41: 'l/h', 42: 'm3/h', 43: 'm3xC',
    44: 'ton', 45: 'ton/h', 46: 'h', 47: 'hh:mm:ss', 48: 'yy:mm:dd',
    49: 'yyyy:mm:dd', 50: 'mm:dd', 51: '', 52: 'bar', 53: 'RTC',
    54: 'ASCII', 55: 'm3 x 10', 56: 'ton x 10', 57: 'GJ x 10',
    58: 'minutes', 59: 'Bitfield', 60: 's', 61: 'ms', 62: 'days',
    63: 'RTC-Q', 64: 'Datetime'
}

def crc_1021(message):
        poly = 0x1021
        reg = 0x0000
        for byte in message:
                mask = 0x80
                while(mask > 0):
                        reg<<=1
                        if byte & mask:
                                reg |= 1
                        mask>>=1
                        if reg & 0x10000:
                                reg &= 0xffff
                                reg ^= poly
        return reg

escapes = {
    0x06: True,
    0x0d: True,
    0x1b: True,
    0x40: True,
    0x80: True,
}

class kamstrup(object):

    def __init__(self, serial_port):
        self.debug_fd = open("/tmp/_kamstrup", "a")
        self.debug_fd.write("\n\nStart\n")
        self.debug_id = None

        self.ser = serial.Serial(
            port = serial_port,
            baudrate = 1200,
            timeout = 2.0)

    def debug(self, dir, b):
        for i in b:
            if dir != self.debug_id:
                if self.debug_id != None:
                    self.debug_fd.write("\n")
                self.debug_fd.write(dir + "\t")
                self.debug_id = dir
            self.debug_fd.write(" %02x " % i)
        self.debug_fd.flush()

    def debug_msg(self, msg):
        if self.debug_id != None:
            self.debug_fd.write("\n")
        self.debug_id = "Msg"
        self.debug_fd.write("Msg\t" + msg)
        self.debug_fd.flush()

    def wr(self, b):
        b = bytearray(b)
        self.debug("Wr", b);
        self.ser.write(b)

    def rd(self):
        a = self.ser.read(1)
        if len(a) == 0:
            self.debug_msg("Rx Timeout")
            return None
        b = bytearray(a)[0]
        self.debug("Rd", bytearray((b,)));
        return b

    def send(self, pfx, msg):
        b = bytearray(msg)

        b.append(0)
        b.append(0)
        c = crc_1021(b)
        b[-2] = c >> 8
        b[-1] = c & 0xff

        c = bytearray()
        c.append(pfx)
        for i in b:
            if i in escapes:
                c.append(0x1b)
                c.append(i ^ 0xff)
            else:
                c.append(i)
        c.append(0x0d)
        self.wr(c)

    def recv(self):
        b = bytearray()
        while True:
            d = self.rd()
            if d == None:
                return None
            if d == 0x40:
                b = bytearray()
            b.append(d)
            if d == 0x0d:
                break
        c = bytearray()
        i = 1;
        while i < len(b) - 1:
            if b[i] == 0x1b:
                v = b[i + 1] ^ 0xff
                if v not in escapes:
                    self.debug_msg(
                        "Missing Escape %02x" % v)
                c.append(v)
                i += 2
            else:
                c.append(b[i])
                i += 1
        if crc_1021(c):
            self.debug_msg("CRC error")
        return c[:-2]

    def readvar(self, nbr):

        self.send(0x80, (0x3f, 0x10, 0x01, nbr >> 8, nbr & 0xff))

        b = self.recv()
        if b == None:
            return (None, None)

        if b[0] != 0x3f or b[1] != 0x10:
            return (None, None)

        if b[2] != nbr >> 8 or b[3] != nbr & 0xff:
            return (None, None)

        if b[4] in units:
            u = units[b[4]]
        else:
            u = None

        # Decode the mantissa
        x = 0
        for i in range(0,b[5]):
            x <<= 8
            x |= b[i + 7]

        # Decode the exponent
        i = b[6] & 0x3f
        if b[6] & 0x40:
            i = -i
        i = math.pow(10,i)
        if b[6] & 0x80:
            i = -i
        x *= i

        if False:
            # Debug print
            s = ""
            for i in b[:4]:
                s += " %02x" % i
            s += " |"
            for i in b[4:7]:
                s += " %02x" % i
            s += " |"
            for i in b[7:]:
                s += " %02x" % i

            print(s, "=", x, units[b[4]])

        return (x, u)


if __name__ == "__main__":
    foo = kamstrup('/dev/ttyUSB0')

    value,unit = foo.readvar(60)
    client.publish("kamstrup/gj",float(value))
    print(float(value))
    value,unit = foo.readvar(86)
    client.publish("kamstrup/temp1",float(value))
    print(float(value))
    value,unit = foo.readvar(87)
    client.publish("kamstrup/temp2",float(value))
    print(float(value))
    value,unit = foo.readvar(74)
    client.publish("kamstrup/flow",float(value))
    print(float(value))
