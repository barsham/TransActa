package com.sillypostilion.processor;

import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOException;
import org.jpos.iso.ISOSource;
import org.jpos.iso.ISORequestListener;
import org.jpos.iso.ISOUtil;
import org.jpos.util.Log;
import org.jpos.util.Logger;
import org.jpos.util.LogEvent;
import org.jpos.core.Configuration;
import org.jpos.core.ConfigurationException;
import org.jpos.q2.QBeanSupport;

import com.sillypostilion.util.DatabaseLogger;
import java.io.IOException;
import java.util.Date;

/**
 * Transaction Processor that processes incoming AS2805 messages
 * and generates appropriate responses
 */
public class TransactionProcessor extends QBeanSupport implements ISORequestListener {
    private DatabaseLogger dbLogger;

    public TransactionProcessor() {
        dbLogger = new DatabaseLogger();
    }

    @Override
    public void setConfiguration(Configuration cfg) throws ConfigurationException {
        super.setConfiguration(cfg);
        // Configure the database logger
        dbLogger.setConfiguration(cfg);
    }

    @Override
    public boolean process(ISOSource source, ISOMsg message) {
        LogEvent evt = new LogEvent(this, "transaction-process");
        try {
            // Log the incoming message
            evt.addMessage("Received message: " + message.getMTI());
            
            // Extract the message type
            String mti = message.getMTI();
            
            // Log transaction details to database
            String transactionId = generateTransactionId();
            dbLogger.logTransaction(transactionId, message, "RECEIVED");
            
            // Process based on message type
            ISOMsg response = null;
            
            if ("0100".equals(mti) || "0200".equals(mti)) {
                // Authorization request or Financial request
                response = processFinancialRequest(message);
            } else if ("0400".equals(mti)) {
                // Reversal
                response = processReversal(message);
            } else if ("0800".equals(mti)) {
                // Network management
                response = processNetworkManagement(message);
            } else {
                // Unsupported message type
                response = createErrorResponse(message, "96", "Unsupported message type");
            }
            
            // Set common response fields
            if (response != null) {
                setCommonResponseFields(message, response);
                
                // Log the response
                dbLogger.logTransaction(transactionId, response, "SENT");
                
                evt.addMessage("Sending response: " + response.getMTI());
                
                // Send the response
                source.send(response);
            }
            
            return true;
        } catch (Exception e) {
            evt.addMessage(e);
            try {
                // Create and send an error response
                ISOMsg errorResponse = createErrorResponse(message, "96", "System error");
                setCommonResponseFields(message, errorResponse);
                source.send(errorResponse);
            } catch (Exception ex) {
                evt.addMessage("Failed to send error response: " + ex.getMessage());
            }
            return false;
        } finally {
            Logger.log(evt);
        }
    }

    /**
     * Process a financial request (0100 or 0200)
     */
    private ISOMsg processFinancialRequest(ISOMsg message) throws ISOException {
        ISOMsg response = (ISOMsg) message.clone();
        
        // Change MTI from request to response
        String originalMti = message.getMTI();
        String responseMti = originalMti.substring(0, 2) + "10";
        response.setMTI(responseMti);
        
        // Simulate transaction processing logic
        String processingCode = message.getString(3);
        String amount = message.getString(4);
        
        // Simple approval logic (in a real system this would involve actual processing)
        if (amount != null && Long.parseLong(amount) < 1000000) {
            // Approve transaction
            response.set(39, "00"); // Approval code
            response.set(38, generateApprovalCode()); // Auth code
        } else {
            // Decline transaction
            response.set(39, "05"); // Do not honor
        }
        
        return response;
    }

    /**
     * Process a reversal request (0400)
     */
    private ISOMsg processReversal(ISOMsg message) throws ISOException {
        ISOMsg response = (ISOMsg) message.clone();
        
        // Change MTI from request to response
        response.setMTI("0410");
        
        // Simulate reversal processing (in a real system this would involve actual reversal)
        response.set(39, "00"); // Approval code
        
        return response;
    }

    /**
     * Process a network management request (0800)
     */
    private ISOMsg processNetworkManagement(ISOMsg message) throws ISOException {
        ISOMsg response = (ISOMsg) message.clone();
        
        // Change MTI from request to response
        response.setMTI("0810");
        
        // Process network management message
        String networkMgmtCode = message.getString(70);
        
        if ("001".equals(networkMgmtCode)) {
            // Sign-on message
            response.set(39, "00"); // Approved
        } else if ("002".equals(networkMgmtCode)) {
            // Sign-off message
            response.set(39, "00"); // Approved
        } else if ("301".equals(networkMgmtCode)) {
            // Echo test
            response.set(39, "00"); // Approved
        } else {
            // Unknown network management code
            response.set(39, "96"); // System error
        }
        
        return response;
    }

    /**
     * Create an error response
     */
    private ISOMsg createErrorResponse(ISOMsg message, String responseCode, String errorDetails) throws ISOException {
        ISOMsg response = (ISOMsg) message.clone();
        
        // Set MTI to response type
        String originalMti = message.getMTI();
        String responseMti = originalMti.substring(0, 2) + "10";
        response.setMTI(responseMti);
        
        // Set error response code
        response.set(39, responseCode);
        
        // Log error details
        LogEvent evt = new LogEvent(this, "error-response");
        evt.addMessage(errorDetails);
        Logger.log(evt);
        
        return response;
    }

    /**
     * Set common fields in the response message
     */
    private void setCommonResponseFields(ISOMsg request, ISOMsg response) throws ISOException {
        // Set current timestamp
        response.set(7, ISOUtil.formatDate(new Date(), "MMddHHmmss"));
        
        // Ensure STAN and other fields are copied from request if not in response
        if (response.getValue(11) == null && request.getValue(11) != null) {
            response.set(11, request.getString(11)); // STAN
        }
        
        // Set trace fields for reconciliation
        if (request.getValue(37) != null) {
            response.set(37, request.getString(37)); // Retrieval reference number
        } else {
            response.set(37, generateRRN());
        }
    }

    /**
     * Generate a transaction ID
     */
    private String generateTransactionId() {
        return "TX" + System.currentTimeMillis() + String.format("%04d", (int)(Math.random() * 10000));
    }

    /**
     * Generate an approval code
     */
    private String generateApprovalCode() {
        return String.format("%06d", (int)(Math.random() * 1000000));
    }

    /**
     * Generate a retrieval reference number
     */
    private String generateRRN() {
        return String.format("%012d", System.currentTimeMillis() % 1000000000000L);
    }
}
