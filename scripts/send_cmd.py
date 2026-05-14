import serial

ser = serial.Serial("/dev/ttyUSB0", 115200)

# envie de me flusher le buffer
# ~ Eric Lecktackone (100% j'ai mal écrit ça)
while ser.in_waiting:
    print(ser.readLine())

ser.write(bytearray(input("Send message : "), encoding='ascii'))

while True:
    print(ser.readline())

