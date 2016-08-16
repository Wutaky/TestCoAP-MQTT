import time, io

import paho.mqtt.client as mqtt

from PIL import Image

start_time = 0

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_message(mqttc, obj, msg):
	global start_time
	print str(int(round(time.time() * 1000)) - start_time) + ' ms (from publishing to receiving image bytearray)'
	img = Image.open(io.BytesIO(msg.payload))
	img.save('new.jpg', 'JPEG', quality=100)
	# img.show()
	img.close()

def on_process(mqttc, obj, msg):
	global start_time
	start_time = int(round(time.time() * 1000))
	print 'Received notification. The publisher starts publishing.'


mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("192.168.0.100", 1883)
mqttc.subscribe('big-data-block', 1)
mqttc.subscribe('notify', 1)
mqttc.message_callback_add('notify', on_process)

mqttc.loop_forever()