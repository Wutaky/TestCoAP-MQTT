import sys, time, datetime

import paho.mqtt.client as mqtt

from grovepi import *

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.connect("192.168.0.100", 1883)

mqttc.loop_start()

dht_sensor_port = 2     # Connect the DHt sensor to port 2
dht_sensor_type = 0

while True:
    [ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)
    payload = "MQTT Message:\n" + datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "\ntemp = %.01fC\nhumidity = %.01f%%"%(temp, hum)
    (rc, mid) = mqttc.publish("topic/temp-and-humi", payload, qos = 1)
    time.sleep(10)