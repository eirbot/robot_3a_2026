import serial

ser = serial.Serial("/dev/ttyUSB0", 115200)
while ser.in_waiting:
    print(ser.readLine())
ser.write(bytearray(input("Send message : "), encoding='ascii'))

while True:
    print(ser.readline())

