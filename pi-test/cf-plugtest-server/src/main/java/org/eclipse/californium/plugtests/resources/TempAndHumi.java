package org.eclipse.californium.plugtests.resources;

import org.eclipse.californium.core.CoapResource;
import org.eclipse.californium.core.coap.CoAP.Type;
import org.eclipse.californium.core.server.resources.CoapExchange;

import static org.eclipse.californium.core.coap.CoAP.ResponseCode.*;
import static org.eclipse.californium.core.coap.MediaTypeRegistry.*;

import java.util.Timer;
import java.util.TimerTask;

public class TempAndHumi extends CoapResource {

	private byte[] tempAndHumi = null;
	private int dataCf = TEXT_PLAIN;
	
	/*
	 * Constructor for a new TemperatureResource
	 */
	public TempAndHumi() {
		super("temp-and-humi");
		setObservable(true);
		getAttributes().addResourceType("observe");
		getAttributes().setObservable();
		setObserveType(Type.CON);
	}
	
	public void handleGET(CoapExchange exchange) {
		
		exchange.setMaxAge(10);
		exchange.respond(CONTENT, tempAndHumi, dataCf);
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
		tempAndHumi = payload;
		dataCf = format;

		getAttributes().clearContentType();
		getAttributes().addContentType(dataCf);
		
		// signal that resource state changed
		changed();
	}
	
}
