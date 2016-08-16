from grovepi import *

dht_sensor_port = 2		# Connect the DHt sensor to port 2
dht_sensor_type = 0		# change this depending on your sensor type - see header comment

while True:
	try:
		[ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)		#Get the temperature and Humidity from the DHT sensor
		print "temp = %.01fC\thumidity = %.01f%%"%(temp, hum)
		time.sleep(1)
	except (IOError,TypeError) as e:
		print "Error!"
