from gevent import monkey
monkey.patch_all()

import sys

from threading import Thread

from flask import Flask, render_template, redirect, request, flash
from flask_socketio import SocketIO, emit

import paho.mqtt.client as mqtt

from twisted.internet import reactor

import txthings.coap as coap
import txthings.resource as resource

from ipaddress import ip_address


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

class mqttSubscribe(object):
	mqttc = mqtt.Client()

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def on_message(mqttc, obj, msg):
	    print('=====================\nMQTT:\n'+msg.topic+"\n"+str(msg.payload)+'\n=====================')
	    socketio.emit(msg.topic, {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

	def on_subscribe(mqttc, obj, mid, granted_qos):
	    print("Subscribed: "+str(mid)+" "+str(granted_qos))

	def subscribe(self, host, port, topic):
		self.mqttc.connect(host, port)
		self.mqttc.subscribe(topic, 0)
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

    def subscribe(self, host, port, topic):
    	self.host = host
    	self.port = port
    	self.topic = topic
    	if not reactor.running:
    		reactor.listenUDP(61616, self.protocol)
    		reactor.callLater(0, self.requestResource)
    		reactor.run()
    	else:
    		self.requestResource()

    def requestResource(self):
        request = coap.Message(code=coap.GET)
        request.opt.uri_path = (self.topic,)
        request.opt.observe = 0
        request.remote = (ip_address(self.host), self.port)
        d = self.protocol.request(request, observeCallback = self.printLaterResponse)
        d.addErrback(self.noResponse)

    def printLaterResponse(self, response):
        print('=====================\nCoAP:\n'+self.topic+"\n"+str(response.payload)+'\n=====================')
        socketio.emit(self.topic, {'payload': response.payload}, broadcast = True, namespace = '/socket_test')

    def noResponse(self, failure):
        print('Failed to fetch resource:')
        print(failure)


@app.route('/unsubscribe/', methods = ['GET'])
def unsubscribe():
	mqtt_sub = mqttSubscribe()
	mqtt_sub.unsubscribe()
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

		if validation:
			if not empty_1:
				mqtt_sub = mqttSubscribe()
				global mqtt_thread
				mqtt_thread = Thread(target = mqtt_sub.subscribe, args = [host_1, port_1, topic_1])
				mqtt_thread.start()				
			if not empty_2:
				coap_sub = coapSubcribe()
				global coap_thread
				coap_thread = Thread(target = coap_sub.subscribe, args = [host_2, port_2, topic_2])
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
    import datetime
    emit(message['channel'], {'payload': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' :: ' + message['data']}, broadcast = True)


if __name__ == '__main__':
	socketio.run(app, debug = True)