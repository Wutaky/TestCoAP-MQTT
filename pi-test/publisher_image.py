import paho.mqtt.client as mqtt

import time

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

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

# while True:
	mqttc.publish("notify", "start", 1)
	mqttc.publish("big-data-block", array ,1)
	# time.sleep(10)
	mqttc.loop_stop()