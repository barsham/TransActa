package com.sillypostilion.api;

import com.sillypostilion.util.DatabaseLogger;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import org.apache.log4j.Logger;
import org.json.simple.JSONObject;
import org.json.simple.JSONArray;

/**
 * API Server that provides REST endpoints for the web portal
 * to access transaction data and system status
 */
public class ApiServer {
    private static final Logger logger = Logger.getLogger(ApiServer.class);
    private static final int PORT = 8000;
    private HttpServer server;
    private DatabaseLogger dbLogger;

    public ApiServer() {
        dbLogger = new DatabaseLogger();
    }

    public void start() {
        try {
            server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);
            
            // Set up context handlers for different API endpoints
            server.createContext("/api/status", new StatusHandler());
            server.createContext("/api/transactions", new TransactionsHandler());
            server.createContext("/api/stats", new StatsHandler());
            
            // Set up thread pool for handling requests
            server.setExecutor(Executors.newFixedThreadPool(10));
            
            // Start the server
            server.start();
            
            logger.info("API Server started on port " + PORT);
        } catch (IOException e) {
            logger.error("Error starting API server", e);
        }
    }

    public void stop() {
        if (server != null) {
            server.stop(0);
            logger.info("API Server stopped");
        }
    }

    /**
     * Handler for /api/status endpoint
     */
    class StatusHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                // Set CORS headers
                exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
                
                if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                    handleOptionsRequest(exchange);
                    return;
                }
                
                // Get system status from database
                Map<String, Object> status = dbLogger.getSystemStatus();
                
                // Convert to JSON
                JSONObject json = new JSONObject(status);
                String response = json.toJSONString();
                
                // Send response
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(response.getBytes());
                }
            } catch (Exception e) {
                logger.error("Error handling status request", e);
                String errorResponse = "{\"error\":\"" + e.getMessage() + "\"}";
                exchange.sendResponseHeaders(500, errorResponse.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(errorResponse.getBytes());
                }
            }
        }
    }

    /**
     * Handler for /api/transactions endpoint
     */
    class TransactionsHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                // Set CORS headers
                exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
                
                if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                    handleOptionsRequest(exchange);
                    return;
                }
                
                // Get query parameters
                String query = exchange.getRequestURI().getQuery();
                Map<String, String> params = parseQueryString(query);
                
                // Get limit parameter or default to 50
                int limit = 50;
                if (params.containsKey("limit")) {
                    try {
                        limit = Integer.parseInt(params.get("limit"));
                    } catch (NumberFormatException e) {
                        // Ignore and use default
                    }
                }
                
                // Get transactions from database
                List<Map<String, Object>> transactions = dbLogger.getRecentTransactions(limit);
                
                // Convert to JSON
                JSONArray jsonArray = new JSONArray();
                jsonArray.addAll(transactions);
                String response = jsonArray.toJSONString();
                
                // Send response
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(response.getBytes());
                }
            } catch (Exception e) {
                logger.error("Error handling transactions request", e);
                String errorResponse = "{\"error\":\"" + e.getMessage() + "\"}";
                exchange.sendResponseHeaders(500, errorResponse.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(errorResponse.getBytes());
                }
            }
        }
    }

    /**
     * Handler for /api/stats endpoint
     */
    class StatsHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                // Set CORS headers
                exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
                
                if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                    handleOptionsRequest(exchange);
                    return;
                }
                
                // Get transaction counts by hour
                Map<String, Integer> countsByHour = dbLogger.getTransactionCountsByHour();
                
                // Convert to JSON
                JSONObject json = new JSONObject(countsByHour);
                String response = json.toJSONString();
                
                // Send response
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(response.getBytes());
                }
            } catch (Exception e) {
                logger.error("Error handling stats request", e);
                String errorResponse = "{\"error\":\"" + e.getMessage() + "\"}";
                exchange.sendResponseHeaders(500, errorResponse.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(errorResponse.getBytes());
                }
            }
        }
    }

    /**
     * Handle OPTIONS requests for CORS preflight
     */
    private void handleOptionsRequest(HttpExchange exchange) throws IOException {
        exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "GET, OPTIONS");
        exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
        exchange.sendResponseHeaders(204, -1);
    }

    /**
     * Parse query string into a map of parameters
     */
    private Map<String, String> parseQueryString(String query) {
        Map<String, String> params = new HashMap<>();
        if (query != null && !query.isEmpty()) {
            String[] pairs = query.split("&");
            for (String pair : pairs) {
                String[] keyValue = pair.split("=");
                if (keyValue.length == 2) {
                    params.put(keyValue[0], keyValue[1]);
                }
            }
        }
        return params;
    }
}
