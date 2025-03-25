package com.sillypostilion;

import org.jpos.q2.Q2;
import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;
import com.sillypostilion.api.ApiServer;

/**
 * SillyPostilion - Transaction Processing System
 * Main application entry point that starts the JPOS Q2 container
 */
public class App {
    private static final Logger logger = Logger.getLogger(App.class);

    public static void main(String[] args) {
        try {
            BasicConfigurator.configure();
            logger.info("Starting SillyPostilion Transaction Processing System...");
            
            // Start the Q2 container
            Q2 q2 = new Q2("deploy");
            q2.start();
            
            // Start the API server
            ApiServer apiServer = new ApiServer();
            apiServer.start();
            
            logger.info("SillyPostilion Transaction Processing System is running");
            logger.info("Press Ctrl-C to stop");
            
            // Keep the application running
            q2.join();
        } catch (Exception e) {
            logger.error("Error starting SillyPostilion", e);
        }
    }
}
