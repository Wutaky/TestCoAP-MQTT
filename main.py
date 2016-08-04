from flask import Flask, render_template, request
from mqtt_subscriber import m_subscribe
# from coap_client_GET import c_client
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dr237*!34R@34t24'
socketio = SocketIO(app)

@app.route('/')
def homepage():
	return render_template('test.html')

@app.route('/subscribe/', methods = ['POST'])
def subscribe():
	protocol = request.form['protocol']
	host = request.form['host']
	port = int(request.form['port'])
	# topic = 'topic/temp-and-humi'
	topic = request.form["topic"]
	if protocol == 'MQTT':
		m_subscribe(host, port, topic)
		pass
	result = {'protocol': protocol,
			  'host': host,
			  'port': port,
			  'topic': topic
			  }
	return render_template('test_result.html', result = result)

@app.route('/chat/', methods = ['GET'])
def chat():
	return render_template('chat.html')

@socketio.on('send_message', namespace = '/socket_test')
def test_message(message):
    import datetime
    emit('echo', {'payload': datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '::' + message['data']}, broadcast = True)


if __name__ == '__main__':
	socketio.run(app, debug = True)