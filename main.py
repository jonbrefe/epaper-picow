from machine import Pin, SPI, I2C
import framebuf
import utime
import network
import socket
import time
import re
import gc
from epaper2in9 import EPD_2in9_Landscape
from config import Params

ssid = Params['WIFI_SSID']
password = Params['WIFI_Password']
Maximum_Rows=Params['Maximum_Rows']
port = Params['Port']
messages = []



wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
 
html = """<!DOCTYPE html>
<html>
  <head> <title>epaper 29 raspberry pi pico w</title> </head>
  <body> <h1>Show message in screen</h1>
    <p>%s</p>
  </body>
</html>
"""
 
# Wait for connect or fail
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  print('waiting for connection...')
  time.sleep(1)
 
# Handle connection error
if wlan.status() != 3:
  raise RuntimeError('network connection failed')
else:
  print('connected')
  status = wlan.ifconfig()
  print( 'ip = ' + status[0] )
 
# Open socket
addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(5)

epd = EPD_2in9_Landscape()
epd.fill(0xff)
epd.text('Listening on', 7, 13, 0x00)
epd.text(str(status[0]), 7, 30, 0x00)

print('listening on', addr)
epd.display_Base(epd.buffer)

# Select the onboard LED
led = machine.Pin("LED", machine.Pin.OUT)

while(1):
    cl, addr = s.accept()
    print('client connected from', addr)
    request = cl.recv(1024)
    print(request)
    request = str(request)
    led.value(1)

    
    print("Original" + str(str(request).split("\\r\\n")))
    payload=request.split("\\r\\n")[0].split()[1].split("/")
    action=payload[1]
    html_encoded_text=payload[2] if len(payload) > 2 else ''
    
    if "message" in action:
         print ("html_encoded_text:" + html_encoded_text)
         message = re.sub("%(..)", lambda m: chr(int(m.group(1), 16)), html_encoded_text)
         print ("message:" + message)
         response = html % messages
         cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
         cl.send(response)
         cl.close()
         #epd.init()
         #epd.Clear(0xff)
         epd.fill(0xff)
         if len(messages) >= Maximum_Rows:
                messages.pop(0)
         messages.append(message)
         last_messages = messages[-10:]
         row=10
         for i, message in enumerate(last_messages):
              epd.text(message, 5, row, 0x00)
              row+=10
         epd.display_Base(epd.buffer)
     
    elif "clean" in action:
         response = html % messages
         cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
         cl.send(response)
         cl.close()
         epd.init()
         epd.Clear(0xff)
         message = "Clean"
    elif "reset" in action:
         response = html % messages
         messages = []
         cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
         cl.send(response)
         cl.close()
         epd.init()
         epd.Clear(0xff)
         message = "Reset"
    else:
         response = html % messages
         messages = []
         cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\No data')
         cl.send(response)
         cl.close()

    # Get the number of bytes of available heap space
    free_bytes = gc.mem_free()

    # Get the number of bytes currently allocated on the heap
    allocated_bytes = gc.mem_alloc()

    # Print the memory usage information
    print("Free memory: {} bytes".format(free_bytes))
    print("Allocated memory: {} bytes".format(allocated_bytes))

    
    
    led.value(0)
