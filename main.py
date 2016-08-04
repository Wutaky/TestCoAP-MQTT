from gevent import monkey
monkey.patch_all()

import sys
import paho.mqtt.client as mqtt

from flask import Flask, render_template, redirect, request, flash
from flask_socketio import SocketIO, emit
# from coap_client_GET import c_client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


class MQTT_subscribe(object):
	mqttc = mqtt.Client()	

	def on_connect(mqttc, obj, flags, rc):
	    print("rc: "+str(rc))

	def on_message(mqttc, obj, msg):
	    print(msg.topic+"\n"+str(msg.payload))
	    socketio.emit('echo', {'payload': msg.payload}, broadcast = True, namespace = '/socket_test')

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


@app.route('/', methods = ['GET', 'POST'])
def homepage():	
	if request.method == 'POST':
		protocol = request.form['protocol']
		host = request.form['host']
		port = request.form['port']
		topic = request.form["topic"]
		validation = True

		if host.strip() == '':
			validation = False
			flash('Host can not be empty!')
		if port.strip() == '':
			validation = False
			flash('Port can not be empty!')
		if not port.isdigit() and port > 9999:
			validation = False
			flash('Wrong port!')
		if topic.strip() == '':
			validation = False
			flash('Topic can not be empty!')

		result = {'protocol': protocol,
				  'host': host,
				  'port': port,
				  'topic': topic
				  }
		if validation:
			port = int(port)
			if protocol == 'MQTT':
				m_sub = MQTT_subscribe()
				m_sub.subscribe(host, port, topic)
			return render_template('test_result.html', result = result)
		else:
			return render_template('test.html', result = result)
	else:
		result = {'host': '',
			  'port': '',
			  'topic': ''
			  }
		return render_template('test.html', result = result)


@app.route('/unsubscribe/', methods = ['GET'])
def unsubscribe():
	m_sub = MQTT_subscribe()
	m_sub.unsubscribe()
	return redirect('/')


@app.route('/chat/', methods = ['GET'])
def chat():
	return render_template('chat.html')


@socketio.on('send_message', namespace = '/socket_test')
def test_message(message):
    import datetime
    emit('echo', {'payload': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + ' :: ' + message['data']}, broadcast = True)


if __name__ == '__main__':
	socketio.run(app, debug = True)