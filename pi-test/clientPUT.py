import sys, datetime

from twisted.internet import reactor, task
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource

from ipaddress import ip_address

from grovepi import *

class Agent():
    """
    Example class which performs single PUT request to iot.eclipse.org
    port 5683 (official IANA assigned CoAP port), URI "/temp-and-humi".
    Request is sent 1 second after initialization.

    Payload is bigger than 64 bytes, and with default settings it
    should be sent as several blocks.
    """

    def __init__(self, protocol):
        self.protocol = protocol
        reactor.callLater(1, self.putResource)

        loop = task.LoopingCall(self.putResource)
        loop.start(10)   # call ten seconds

    def putResource(self):
        dht_sensor_port = 2     # Connect the DHt sensor to port 2
        dht_sensor_type = 0
        [ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)
        payload = "CoAP Message:\n" + datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + "\ntemp = %.01fC\nhumidity = %.01f%%"%(temp, hum)
        request = coap.Message(code=coap.PUT, payload=payload)
        request.opt.uri_path = ("temp-and-humi",)
        request.opt.content_format = coap.media_types_rev['text/plain']
        request.remote = (ip_address('192.168.0.100'), coap.COAP_PORT)
        d = protocol.request(request)
        d.addCallback(self.printResponse)

    def printResponse(self, response):
        print 'Response Code: ' + coap.responses[response.code]
        print 'Payload: ' + response.payload    

log.startLogging(sys.stdout)

endpoint = resource.Endpoint(None)
protocol = coap.Coap(endpoint)
client = Agent(protocol)

reactor.listenUDP(61616, protocol)
reactor.run()