import paho.mqtt.client as mqtt

import time

start_time = 0

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))
    global start_time
    print str(int(round(time.time() * 1000)) - start_time) + ' ms'

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.connect("192.168.0.100")

mqttc.loop_start()

with open("021.jpg", "rb") as imageFile:
	file = imageFile.read()
	array = bytearray(file)
	imageFile.close()
	# print len(array)

while True:
	# mqttc.publish("notify", "start", 1)
	start_time = int(round(time.time() * 1000))
	mqttc.publish("big-data-block", array , 1)
	time.sleep(15)
	# mqttc.loop_stop()