package com.sillypostilion.server;

import java.io.IOException;
import org.jpos.iso.ISOException;
import org.jpos.iso.ISOServer;
import org.jpos.iso.ServerChannel;
import org.jpos.iso.channel.ASCIIChannel;
import org.jpos.q2.QBeanSupport;
import org.jpos.util.LogSource;
import org.jpos.util.NameRegistrar;
import org.jpos.core.Configuration;
import org.jpos.core.ConfigurationException;

import com.sillypostilion.message.AS2805MessageFactory;
import com.sillypostilion.message.AS2805Packager;
import com.sillypostilion.processor.TransactionProcessor;

/**
 * Transaction Server that listens for incoming AS2805 messages
 * over TCP/IP connections
 */
public class TransactionServer extends QBeanSupport implements Runnable {
    private ISOServer server;
    private int port;
    private int maxSessions;
    private String channelName;

    @Override
    public void init() throws ConfigurationException {
        Configuration cfg = getConfiguration();
        port = cfg.getInt("port", 8000);
        maxSessions = cfg.getInt("max-sessions", 100);
        channelName = cfg.get("channel-name", "as2805-channel");
    }

    @Override
    public void start() {
        try {
            // Create the AS2805 packager
            AS2805Packager packager = new AS2805Packager();
            
            // Create the message factory to handle AS2805 messages
            AS2805MessageFactory msgFactory = new AS2805MessageFactory();
            msgFactory.setPackager(packager);
            
            // Create the transaction processor
            TransactionProcessor processor = new TransactionProcessor();
            
            // Create a channel prototype
            ServerChannel channel = new ASCIIChannel(packager);
            channel.setName(channelName);
            ((LogSource) channel).setLogger(getLog().getLogger(), "channel");
            
            // Create the ISO server
            server = new ISOServer(port, channel, null);
            server.setMaxSessions(maxSessions);
            server.setLogger(getLog().getLogger(), "server");
            server.setMessageFactory(msgFactory);
            server.addISORequestListener(processor);
            
            // Register server with NameRegistrar
            NameRegistrar.register("server." + getName(), server);
            
            // Start the server in a separate thread
            new Thread(this).start();
            
            log.info("Transaction server started on port " + port);
        } catch (ISOException e) {
            log.error("Error initializing transaction server", e);
        }
    }

    @Override
    public void stop() {
        try {
            if (server != null) {
                server.shutdown();
                NameRegistrar.unregister("server." + getName());
                log.info("Transaction server stopped");
            }
        } catch (Exception e) {
            log.error("Error stopping transaction server", e);
        }
    }

    @Override
    public void run() {
        try {
            server.serve();
        } catch (IOException e) {
            log.error("Error in server operation", e);
        }
    }
}
