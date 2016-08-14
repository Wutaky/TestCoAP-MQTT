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

mqtt_start_time = 0

class mqttPublish(object):
	mqttc = mqtt.Client()

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def publish(self, host, port, topic, topic_p):
		self.mqttc.connect(host, port)
		self.mqttc.loop_start()
		while True:
			global mqtt_start_time
			mqtt_start_time = int(round(time.time() * 1000))
			self.mqttc.publish(topic_p, 'ping', qos = 1)
			time.sleep(2)

	def stopPublish(self):
		self.mqttc.loop_stop()

	mqttc.on_connect = on_connect


class mqttSubscribe(object):
	mqttc = mqtt.Client()

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def on_message(mqttc, obj, msg):
	    print('=====================\nMQTT:\n'+msg.topic+"\n"+str(msg.payload)+'\n=====================')
	    socketio.emit('MQTT/' + msg.topic, {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

	def on_ping_test(self, mqttc, obj, msg):
		end_time = int(round(time.time() * 1000))
		latency = end_time - mqtt_start_time
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

    def subscribe(self, host, port, topic, topic_p):
    	self.host = host
    	self.port = port
    	self.topic = topic
    	self.topic_p = topic_p

    	global loop
    	loop = task.LoopingCall(self.putResource)
        loop.start(2)

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
        d_p = self.protocol.request(request_p, observeCallback = self.pingResponse)
        d_p.addErrback(self.noResponse)  

    def putResource(self):
    	self.start_time = int(round(time.time() * 1000))
    	payload = self.topic_p + datetime.datetime.today().strftime("%S")
        request = coap.Message(code = coap.PUT, payload = payload)
        request.opt.uri_path = ("ping-test",)
        request.opt.content_format = coap.media_types_rev['text/plain']
        request.remote = (ip_address(self.host), self.port)        
        d = self.protocol.request(request)

    def outputResponse(self, response):
        print('=====================\nCoAP:\n'+self.topic+"\n"+str(response.payload)+'\n=====================')
        socketio.emit('CoAP/' + self.topic, {'payload': response.payload}, broadcast = True, namespace = '/socket_test')

    def pingResponse(self, response):
    	payload = response.payload

    	if payload[:4] == self.topic_p and payload[-2:] != self.last_start_second:
    		latency = int(round(time.time() * 1000)) - self.start_time
    		self.last_start_second = payload[-2:]
    		
    		socketio.emit('CoAP/ping', {'latency': latency}, broadcast = True, namespace = '/socket_test')

    def noResponse(self, failure):
        print('Failed to fetch resource:')
        print(failure)


@app.route('/unsubscribe/', methods = ['GET'])
def unsubscribe():
	mqtt_sub = mqttSubscribe()
	mqtt_sub.unsubscribe()
	mqtt_pub = mqttPublish()
	mqtt_pub.stopPublish()
	if coap_thread.isAlive():
		loop.stop()
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
				  'empty_2': empty_2
				  }
		topic_p = 'p' + str(random.randint(100, 999))
		if validation:
			if not empty_1:
				mqtt_pub = mqttPublish()
				mqtt_pub_thread = threading.Thread(target = mqtt_pub.publish, args = [host_1, port_1, topic_1, topic_p])

				mqtt_sub = mqttSubscribe()
				mqtt_sub_thread = threading.Thread(target = mqtt_sub.subscribe, args = [host_1, port_1, topic_1, topic_p])

				mqtt_pub_thread.start()
				mqtt_sub_thread.start()
			if not empty_2:
				coap_sub = coapSubcribe()
				global coap_thread
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