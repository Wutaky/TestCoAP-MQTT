package org.eclipse.californium.plugtests.resources;

import static org.eclipse.californium.core.coap.CoAP.ResponseCode.BAD_REQUEST;
import static org.eclipse.californium.core.coap.CoAP.ResponseCode.CHANGED;
import static org.eclipse.californium.core.coap.CoAP.ResponseCode.CONTENT;
import static org.eclipse.californium.core.coap.CoAP.ResponseCode.NOT_ACCEPTABLE;
import static org.eclipse.californium.core.coap.MediaTypeRegistry.APPLICATION_OCTET_STREAM;

import org.eclipse.californium.core.CoapResource;
import org.eclipse.californium.core.coap.CoAP.Type;
import org.eclipse.californium.core.server.resources.CoapExchange;

public class BlockTest extends CoapResource {
	
	private byte[] blockTest = null;
	private int dataCf = APPLICATION_OCTET_STREAM;
	
	/*
	 * Constructor for a new TemperatureResource
	 */
	public BlockTest() {
		super("block-test");
		setObservable(true);
		getAttributes().addResourceType("observe");
		getAttributes().setObservable();
		setObserveType(Type.CON);
	}
	
	public void handleGET(CoapExchange exchange) {
		
		exchange.setMaxAge(10);
		exchange.respond(CONTENT, blockTest, dataCf);
	}

	public void handlePUT(CoapExchange exchange) {
		
		if (!exchange.getRequestOptions().hasContentFormat()) {
			exchange.respond(BAD_REQUEST, "Content-Format not set");
			return;
		}
		
		// store payload
		storeData(exchange.getRequestPayload(), exchange.getRequestOptions().getContentFormat());

		// complete the request
		exchange.respond(CHANGED);
	}
	
	// Internal ////////////////////////////////////////////////////////////////
	
	/*
	 * Convenience function to store data contained in a 
	 * PUT/POST-Request. Notifies observing endpoints about
	 * the change of its contents.
	 */
	private synchronized void storeData(byte[] payload, int format) {

		if (format != dataCf) {
			clearAndNotifyObserveRelations(NOT_ACCEPTABLE);
		}
		
		// set payload and content type
		blockTest = payload;
		dataCf = format;

		getAttributes().clearContentType();
		getAttributes().addContentType(dataCf);
		
		// signal that resource state changed
		changed();
	}

}
