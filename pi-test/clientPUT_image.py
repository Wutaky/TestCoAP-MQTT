import sys, io, time

from twisted.internet import reactor, task
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource

from ipaddress import ip_address

from PIL import Image

class Agent():
    """
    Example class which performs single PUT request to iot.eclipse.org
    port 5683 (official IANA assigned CoAP port), URI "/temp-and-humi".
    Request is sent 1 second after initialization.

    Payload is bigger than 64 bytes, and with default settings it
    should be sent as several blocks.
    """
    with open("021.jpg", "rb") as imageFile:
        file = imageFile.read()
        array = bytearray(file)
        imageFile.close()

    start_time = 0

    def __init__(self, protocol):
        self.protocol = protocol
        reactor.callLater(1, self.putResource)

        loop = task.LoopingCall(self.putResource)
        loop.start(15)

    def putResource(self):
        request = coap.Message(code = coap.PUT, payload = self.array)
        request.opt.uri_path = ("block-test",)
        request.opt.content_format = coap.media_types_rev['application/octet-stream']
        request.remote = (ip_address('192.168.0.100'), coap.COAP_PORT)
        print 'Start uploading...'
        self.start_time = int(round(time.time() * 1000))
        d = protocol.request(request)
        d.addCallback(self.on_publish)

    def on_publish(self, response):
        print 'Response Code: ' + coap.responses[response.code]
        print str(int(round(time.time() * 1000)) - self.start_time) + ' ms'

# log.startLogging(sys.stdout)

endpoint = resource.Endpoint(None)
protocol = coap.Coap(endpoint)
client = Agent(protocol)

reactor.listenUDP(51515, protocol)
reactor.run()