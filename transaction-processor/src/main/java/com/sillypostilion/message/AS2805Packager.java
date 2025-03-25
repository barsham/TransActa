package com.sillypostilion.message;

import org.jpos.iso.ISOBasePackager;
import org.jpos.iso.ISOFieldPackager;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOException;
import org.jpos.iso.IFA_AMOUNT;
import org.jpos.iso.IFA_BITMAP;
import org.jpos.iso.IFA_BINARY;
import org.jpos.iso.IFA_LLCHAR;
import org.jpos.iso.IFA_LLLCHAR;
import org.jpos.iso.IFA_LLNUM;
import org.jpos.iso.IFA_NUMERIC;
import org.jpos.iso.IFB_BINARY;
import org.jpos.iso.IFB_BITMAP;
import org.jpos.iso.IFB_LLCHAR;
import org.jpos.iso.IFB_LLLCHAR;
import org.jpos.iso.IFB_LLNUM;
import org.jpos.iso.IFB_NUMERIC;
import org.jpos.iso.ISOUtil;
import org.jpos.iso.packager.GenericPackager;
import java.io.InputStream;

/**
 * AS2805 Message packager that handles the packing and unpacking
 * of AS2805 financial messages
 */
public class AS2805Packager extends GenericPackager {

    public AS2805Packager() throws ISOException {
        super();
        try {
            // Load the packager definition from the XML file
            InputStream is = getClass().getResourceAsStream("/packager/as2805.xml");
            if (is == null) {
                throw new ISOException("Could not find AS2805 packager definition");
            }
            readXmlConfig(is);
        } catch (Exception e) {
            throw new ISOException("Error loading AS2805 packager", e);
        }
    }

    @Override
    public byte[] pack(ISOMsg msg) throws ISOException {
        try {
            // Ensure proper message type for AS2805
            validateAS2805Message(msg);
            
            // Pack the message
            return super.pack(msg);
        } catch (Exception e) {
            throw new ISOException("Error packing AS2805 message", e);
        }
    }

    @Override
    public void unpack(ISOMsg msg, byte[] b) throws ISOException {
        try {
            // Unpack the message
            super.unpack(msg, b);
            
            // Validate the unpacked message conforms to AS2805
            validateAS2805Message(msg);
        } catch (Exception e) {
            throw new ISOException("Error unpacking AS2805 message", e);
        }
    }

    /**
     * Validate that the message conforms to AS2805 standard
     */
    private void validateAS2805Message(ISOMsg msg) throws ISOException {
        // Check for required fields as per AS2805
        if (msg.getMTI() == null) {
            throw new ISOException("Invalid AS2805 message: missing MTI");
        }
        
        // AS2805 requires specific MTI formats (0xxx)
        String mti = msg.getMTI();
        if (!mti.matches("0[0-9]{3}")) {
            throw new ISOException("Invalid AS2805 MTI format: " + mti);
        }
        
        // Additional AS2805-specific validations could go here
    }
}
