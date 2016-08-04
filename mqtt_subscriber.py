#!/usr/bin/python

# This shows a simple example of an MQTT subscriber.

import sys
import paho.mqtt.client as mqtt

from flask.ext.socketio import emit

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_message(mqttc, obj, msg):
    print(msg.topic+"\n"+str(msg.payload))
    emit('echo', {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def m_subscribe(host, port, topic):
	mqttc = mqtt.Client()
	mqttc.on_connect = on_connect
	mqttc.on_subscribe = on_subscribe
	mqttc.on_message = on_message
	mqttc.connect(host, port)
	mqttc.subscribe(topic, 0)

	mqttc.loop_start()

	# mqttc.loop_forever()