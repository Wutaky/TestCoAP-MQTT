import sys, time, io

from twisted.internet import reactor
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource

from ipaddress import ip_address

from PIL import Image

class Agent():
    """
    Example class which performs single GET request to coap.me
    port 5683 (official IANA assigned CoAP port), URI "test".
    Request is sent 1 second after initialization.
    
    Remote IP address is hardcoded - no DNS lookup is preformed.

    Method requestResource constructs the request message to
    remote endpoint. Then it sends the message using protocol.request().
    A deferred 'd' is returned from this operation.

    Deferred 'd' is fired internally by protocol, when complete response is received.

    Method printResponse is added as a callback to the deferred 'd'. This
    method's main purpose is to act upon received response (here it's simple print).
    """

    start_time = 0

    def __init__(self, protocol):
        self.protocol = protocol
        reactor.callLater(0, self.requestResource)

    def requestResource(self):
        request = coap.Message(code = coap.GET)
        #Send request to "coap://192.168.0.101:5683/temp-and-humi"
        request.opt.uri_path = ('temp-and-humi',)
        request.opt.observe = 0
        request.remote = (ip_address("192.168.0.100"), coap.COAP_PORT)
        d = protocol.request(request, observeCallback = self.printLaterResponse)
        d.addErrback(self.noResponse)

    def printLaterResponse(self, response):
        if response.payload == 'start':
            self.start_time = int(round(time.time() * 1000))
            print 'Received notification. The publisher starts publishing.'
        else:
            print str(int(round(time.time() * 1000)) - self.start_time) + ' ms (from publishing to receiving image bytearray)'
            img = Image.open(io.BytesIO(response.payload))
            img.save('new.jpg', 'JPEG', quality = 100)
            # img.show()
            img.close()

    def noResponse(self, failure):
        print 'Failed to fetch resource:'
        print failure

# log.startLogging(sys.stdout)

endpoint = resource.Endpoint(None)
protocol = coap.Coap(endpoint)
client = Agent(protocol)

reactor.listenUDP(61616, protocol)
reactor.run()