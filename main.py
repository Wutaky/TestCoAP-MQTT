from gevent import monkey
monkey.patch_all()

import sys, time, datetime, threading, random

from flask import Flask, render_template, redirect, request, flash
from flask_socketio import SocketIO, emit

import paho.mqtt.client as mqtt

from twisted.internet import reactor, task

import txthings.coap as coap
import txthings.resource as resource

from ipaddress import ip_address


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

mqtt_ping_start_time = 0
mqtt_block_start_time = 0

empty_1 = True
empty_2 = True

with open("static/images/021.jpg", "rb") as imageFile:
    file = imageFile.read()
    global byteArray
    byteArray = bytearray(file)
    imageFile.close()

class mqttPingTest(object):
	mqttc = mqtt.Client()	

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def pingTest(self, host, port, topic_p):
		self.mqttc.connect(host, port)
		self.mqttc.loop_start()
		while True:
			global mqtt_ping_start_time
			mqtt_ping_start_time = int(round(time.time() * 1000))
			self.mqttc.publish(topic_p, 'ping', qos = 1)
			time.sleep(2)	

	def stopPublish(self):
		self.mqttc.loop_stop()

	mqttc.on_connect = on_connect


class mqttBlockTest(object):
	mqttc = mqtt.Client()

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def blockTest(self, host, port):
		self.mqttc.connect(host, port)
		self.mqttc.loop_start()
		while True:
			global mqtt_block_start_time
			mqtt_block_start_time = int(round(time.time() * 1000))
			self.mqttc.publish("big-data-block", byteArray , 1)
			time.sleep(15)

	def on_publish(mqttc, obj, mid):
		timeCost = int(round(time.time() * 1000)) - mqtt_block_start_time
		print 'MQTT Block: ' + str(timeCost) + ' ms'
		socketio.emit('MQTT/block', {'timeCost': timeCost}, broadcast = True, namespace = '/socket_test')

	def stopPublish(self):
		self.mqttc.loop_stop()

	mqttc.on_connect = on_connect
	mqttc.on_publish = on_publish


class mqttSubscribe(object):
	mqttc = mqtt.Client()

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def on_message(mqttc, obj, msg):
	    print('=====================\nMQTT:\n'+msg.topic+"\n"+str(msg.payload)+'\n=====================')
	    socketio.emit('MQTT/' + msg.topic, {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

	def on_ping_test(self, mqttc, obj, msg):
		end_time = int(round(time.time() * 1000))
		latency = end_time - mqtt_ping_start_time
		socketio.emit('MQTT/ping', {'latency': latency}, broadcast = True, namespace = '/socket_test')

	def on_subscribe(mqttc, obj, mid, granted_qos):
	    print("Subscribed: "+str(mid)+" "+str(granted_qos))

	def subscribe(self, host, port, topic, topic_p):
		self.mqttc.connect(host, port)
		self.mqttc.subscribe(topic, 1)
		self.mqttc.subscribe(topic_p, 1)
		self.mqttc.message_callback_add(topic_p, self.on_ping_test)
		self.mqttc.loop_start()

	def unsubscribe(self):
		self.mqttc.loop_stop()

	mqttc.on_connect = on_connect
	mqttc.on_subscribe = on_subscribe
	mqttc.on_message = on_message


class coapSubcribe(object):
    endpoint = resource.Endpoint(None)
    protocol = coap.Coap(endpoint)
    host = ''
    port = 0
    topic = ''
    topic_p = ''
    start_time = 0
    last_start_second = ''
    block_start_time = 0

    def subscribe(self, host, port, topic, topic_p):
    	self.host = host
    	self.port = port
    	self.topic = topic
    	self.topic_p = topic_p

    	global loop_1
    	global loop_2
    	loop_1 = task.LoopingCall(self.pingTestResource)
    	loop_2 = task.LoopingCall(self.blockTestResource)
        loop_1.start(2)
        loop_2.start(15)


    	if not reactor.running:
    		reactor.listenUDP(61616, self.protocol)
    		reactor.callLater(0, self.requestResource)
    		reactor.run()
    	else:
    		reactor.callLater(0, self.requestResource)

    def requestResource(self):
        request = coap.Message(code = coap.GET)
        request.opt.uri_path = (self.topic,)
        request.opt.observe = 0
        request.remote = (ip_address(self.host), self.port)
        d = self.protocol.request(request, observeCallback = self.outputResponse)
        d.addErrback(self.noResponse)

        request_p = coap.Message(code = coap.GET)
        request_p.opt.uri_path = ('ping-test',)
        request_p.opt.observe = 0
        request_p.remote = (ip_address(self.host), self.port)
        d_p = self.protocol.request(request_p, observeCallback = self.pingOutputResponse)
        d_p.addErrback(self.noResponse)  

    def pingTestResource(self):
    	self.start_time = int(round(time.time() * 1000))
    	payload = self.topic_p + datetime.datetime.today().strftime("%S")
        request = coap.Message(code = coap.PUT, payload = payload)
        request.opt.uri_path = ("ping-test",)
        request.opt.content_format = coap.media_types_rev['text/plain']
        request.remote = (ip_address(self.host), self.port)        
        d = self.protocol.request(request)

    def blockTestResource(self):
        request = coap.Message(code = coap.PUT, payload = byteArray)
        request.opt.uri_path = ("block-test",)
        request.opt.content_format = coap.media_types_rev['application/octet-stream']
        request.remote = (ip_address(self.host), self.port)
        self.block_start_time = int(round(time.time() * 1000))
        d = self.protocol.request(request)
        d.addCallback(self.blockOutputResponse)    

    def outputResponse(self, response):
        print('=====================\nCoAP:\n'+self.topic+"\n"+str(response.payload)+'\n=====================')
        socketio.emit('CoAP/' + self.topic, {'payload': response.payload}, broadcast = True, namespace = '/socket_test')

    def pingOutputResponse(self, response):
    	payload = response.payload

    	if payload[:4] == self.topic_p and payload[-2:] != self.last_start_second:
    		latency = int(round(time.time() * 1000)) - self.start_time
    		self.last_start_second = payload[-2:]
    		
    		socketio.emit('CoAP/ping', {'latency': latency}, broadcast = True, namespace = '/socket_test')

    def blockOutputResponse(self, response):
        timeCost = int(round(time.time() * 1000)) - self.block_start_time
        print 'CoAP Block: ' + str(timeCost) + ' ms'
        socketio.emit('CoAP/block', {'timeCost': timeCost}, broadcast = True, namespace = '/socket_test')

    def noResponse(self, failure):
        print('Failed to fetch resource:')
        print(failure)


@app.route('/unsubscribe/', methods = ['GET'])
def unsubscribe():
	if not empty_1:
		mqtt_sub = mqttSubscribe()
		mqtt_sub.unsubscribe()
		mqtt_ping = mqttPingTest()
		mqtt_ping.stopPublish()
		mqtt_block = mqttBlockTest()
		mqtt_block.stopPublish()
	if not empty_2:
		loop_1.stop()
		loop_2.stop()
	return redirect('/')


@app.route('/', methods = ['GET', 'POST'])
def homepage():	
	if request.method == 'POST':
		host_1 = request.form['host_1'].strip()
		port_1 = request.form['port_1'].strip()
		topic_1 = request.form["topic_1"].strip()
		host_2 = request.form['host_2'].strip()
		port_2 = request.form['port_2'].strip()
		topic_2 = request.form["topic_2"].strip()
		validation = True
		global empty_1
		global empty_2
		empty_1 = True
		empty_2 = True

		if port_1.isdigit():
			port_1 = int(port_1)
		if port_2.isdigit():
			port_2 = int(port_2)

		if host_1 != '' or port_1 != '' or topic_1 != '':
			empty_1 = False
		if host_2 != '' or port_2 != '' or topic_2 != '':
			empty_2 = False

		if host_1 == '' and not empty_1 or host_2 == '' and not empty_2 or empty_1 and empty_2: 
			validation = False
			flash('Host can not be empty!')
		if port_1 == '' and not empty_1 or port_2 == '' and not empty_2 or empty_1 and empty_2:
			validation = False
			flash('Port can not be empty!')
		if port_1 != '' or port_2 != '':
			if port_1 > 9999 and not empty_1 or port_2 > 9999 and not empty_2:
				validation = False
				flash('Wrong port!')
		if topic_1 == '' and not empty_1 or topic_2 == '' and not empty_2 or empty_1 and empty_2:
			validation = False
			flash('Topic can not be empty!')

		result = {'host_1': host_1,
				  'port_1': port_1,
				  'topic_1': topic_1,
				  'empty_1': empty_1,
				  'host_2': host_2,
				  'port_2': port_2,
				  'topic_2': topic_2,
				  'empty_2': empty_2,
				  'blockSize': len(byteArray),
				  'blockCf': 'image/jpeg'
				  }
		topic_p = 'p' + str(random.randint(100, 999))
		if validation:
			if not empty_1:
				mqtt_ping = mqttPingTest()
				mqtt_ping_thread = threading.Thread(target = mqtt_ping.pingTest, args = [host_1, port_1, topic_p])

				mqtt_block = mqttBlockTest()
				mqtt_block_thread = threading.Thread(target = mqtt_block.blockTest, args = [host_1, port_1])

				mqtt_sub = mqttSubscribe()
				mqtt_sub_thread = threading.Thread(target = mqtt_sub.subscribe, args = [host_1, port_1, topic_1, topic_p])

				mqtt_ping_thread.start()
				mqtt_block_thread.start()
				mqtt_sub_thread.start()
			if not empty_2:
				coap_sub = coapSubcribe()
				coap_thread = threading.Thread(target = coap_sub.subscribe, args = [host_2, port_2, topic_2, topic_p])
				coap_thread.start()

			return render_template('test_result.html', result = result)
		else:
			return render_template('test.html', result = result)
	else:
		return render_template('test.html', result = {})


@app.route('/chat/<path:channel>/', methods = ['GET'])
def chat(channel = 'default'):
	return render_template('chat.html', channel = channel)


@socketio.on('send_message', namespace = '/socket_test')
def testMessage(message):
    emit(message['channel'], {'payload': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' :: ' + message['data']}, broadcast = True)


if __name__ == '__main__':
	socketio.run(app, debug = True)