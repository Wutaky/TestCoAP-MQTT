from gevent import monkey
monkey.patch_all()

import sys

from flask import Flask, render_template, redirect, request, flash
from flask_socketio import SocketIO, emit

import paho.mqtt.client as mqtt


from twisted.internet import reactor
from twisted.python import log

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
	    print(msg.topic+"\n"+str(msg.payload))
	    socketio.emit('mqtt_echo', {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

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
    # def __init__(self, host, port, topic):
    # 	# log.startLogging(sys.stdout)
    	
    # 	endpoint = resource.Endpoint(None)
    # 	protocol = coap.Coap(endpoint)
    #     self.protocol = protocol
    #     self.host = host
    #     self.port = port
    #     self.topic = topic

    #     reactor.listenUDP(61616, protocol)        
    #     reactor.callLater(0, self.requestResource)
    #     reactor.run()

    endpoint = resource.Endpoint(None)
    protocol = coap.Coap(endpoint)
    host = ''
    port = 0
    topic = ''
    tempReactor = reactor

    def subscribe(self, host, port, topic):
    	self.host = host
        self.port = port
        self.topic = topic
        self.tempReactor.listenUDP(61616, self.protocol)
        self.tempReactor.callLater(0, self.requestResource)
    	self.tempReactor.run()

    def requestResource(self):
        request = coap.Message(code=coap.GET)
        # Send request to "coap://192.168.0.100:5683/temp-and-humi"
        request.opt.uri_path = (self.topic,)
        request.opt.observe = 0
        request.remote = (ip_address(self.host), self.port)
        d = self.protocol.request(request, observeCallback = self.printLaterResponse)
        d.addErrback(self.noResponse)

    def printLaterResponse(self, response):
        print(response.payload)
        socketio.emit('coap_echo', {'payload': response.payload}, broadcast = True, namespace = '/socket_test')

    def noResponse(self, failure):
        print('Failed to fetch resource:')
        print(failure)

    def unsubscribe(self):
    	self.tempReactor.callFromThread(reactor.stop)


@app.route('/unsubscribe/', methods = ['GET'])
def unsubscribe():
	m_sub = mqttSubscribe()
	m_sub.unsubscribe()
	c_sub = coapSubcribe()
	c_sub.unsubscribe()
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
				m_sub = mqttSubscribe()
				m_sub.subscribe(host_1, port_1, topic_1)
			if not empty_2:
				# c_sub = coapSubcribe(host_2, port_2, topic_2)
				c_sub = coapSubcribe()
				c_sub.subscribe(host_2, port_2, topic_2)

			return render_template('test_result.html', result = result)
		else:
			return render_template('test.html', result = result)
	else:
		return render_template('test.html', result = {})


@app.route('/chat/', methods = ['GET'])
def chat():
	return render_template('chat.html')


@socketio.on('send_message', namespace = '/socket_test')
def testMessage(message):
    import datetime
    emit('mqtt_echo', {'payload': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' :: ' + message['data']}, broadcast = True)


if __name__ == '__main__':
	socketio.run(app, debug = True)