package com.sillypostilion.message;

import org.jpos.iso.ISOException;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOPackager;
import org.jpos.iso.ISOUtil;
import org.jpos.iso.ISOMessageFactory;
import org.jpos.iso.header.BaseHeader;
import java.io.IOException;
import java.io.InputStream;

/**
 * Factory for creating AS2805 messages based on the incoming data
 */
public class AS2805MessageFactory implements ISOMessageFactory {
    private ISOPackager packager;

    public AS2805MessageFactory() {
        // Default constructor
    }

    public void setPackager(ISOPackager packager) {
        this.packager = packager;
    }

    @Override
    public ISOMsg createMsg(byte[] b) throws ISOException {
        try {
            // Create a new AS2805 message
            ISOMsg m = new ISOMsg();
            m.setPackager(packager);
            
            // Parse the message
            if (b.length > 0) {
                // Handle message header if present
                if (hasMessageHeader(b)) {
                    // Extract and set the message header
                    byte[] header = new byte[12]; // AS2805 typically has 12-byte header
                    System.arraycopy(b, 0, header, 0, 12);
                    m.setHeader(new BaseHeader(header));
                    
                    // Parse the remaining message body
                    byte[] body = new byte[b.length - 12];
                    System.arraycopy(b, 12, body, 0, body.length);
                    m.unpack(body);
                } else {
                    // No header, unpack the whole message
                    m.unpack(b);
                }
            }
            return m;
        } catch (Exception e) {
            throw new ISOException("Error creating AS2805 message", e);
        }
    }

    @Override
    public ISOMsg createMsg(InputStream in) throws IOException, ISOException {
        try {
            // Read the message bytes from the input stream
            int msgLength = in.available();
            byte[] b = new byte[msgLength];
            in.read(b);
            
            // Create message from the bytes
            return createMsg(b);
        } catch (IOException e) {
            throw new IOException("Error reading AS2805 message from stream", e);
        }
    }

    /**
     * Check if the message contains a header
     * This is a simplified implementation - in a real system you would have
     * more sophisticated logic to determine the presence of a header
     */
    private boolean hasMessageHeader(byte[] b) {
        // Basic check - messages shorter than what would contain a header + content
        return b.length > 24; // arbitrary minimum length for a message with header
    }
}
