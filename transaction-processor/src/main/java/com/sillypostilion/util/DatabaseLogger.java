package com.sillypostilion.util;

import org.jpos.iso.ISOException;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOUtil;
import org.jpos.core.Configuration;
import org.jpos.core.ConfigurationException;
import org.jpos.util.Log;
import org.jpos.util.Logger;
import org.jpos.util.LogEvent;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Database logger for transaction messages
 * Stores transaction details in a database for later retrieval by the web portal
 */
public class DatabaseLogger {
    private String dbUrl;
    private String dbUser;
    private String dbPassword;
    private boolean initialized = false;

    public DatabaseLogger() {
        // Default constructor
    }

    public void setConfiguration(Configuration cfg) throws ConfigurationException {
        dbUrl = cfg.get("db-url", "jdbc:h2:file:./sillypostilion;AUTO_SERVER=TRUE");
        dbUser = cfg.get("db-user", "sa");
        dbPassword = cfg.get("db-password", "");
        
        try {
            initializeDatabase();
        } catch (SQLException e) {
            throw new ConfigurationException("Error initializing database", e);
        }
    }

    /**
     * Initialize the database and create tables if they don't exist
     */
    private void initializeDatabase() throws SQLException {
        if (initialized) {
            return;
        }
        
        try (Connection conn = getConnection()) {
            // Create transactions table
            try (Statement stmt = conn.createStatement()) {
                stmt.execute(
                    "CREATE TABLE IF NOT EXISTS transactions (" +
                    "id VARCHAR(50) PRIMARY KEY, " +
                    "mti VARCHAR(4), " +
                    "processing_code VARCHAR(6), " +
                    "amount VARCHAR(12), " +
                    "transmission_datetime VARCHAR(10), " +
                    "stan VARCHAR(6), " +
                    "rrn VARCHAR(12), " +
                    "response_code VARCHAR(2), " +
                    "terminal_id VARCHAR(8), " +
                    "merchant_id VARCHAR(15), " +
                    "direction VARCHAR(10), " +
                    "raw_message VARCHAR(4000), " +
                    "timestamp TIMESTAMP" +
                    ")"
                );
                
                // Create system status table
                stmt.execute(
                    "CREATE TABLE IF NOT EXISTS system_status (" +
                    "id INT PRIMARY KEY, " +
                    "status VARCHAR(20), " +
                    "start_time TIMESTAMP, " +
                    "transactions_processed BIGINT, " +
                    "last_updated TIMESTAMP" +
                    ")"
                );
                
                // Insert default system status if not exists
                stmt.execute(
                    "MERGE INTO system_status (id, status, start_time, transactions_processed, last_updated) " +
                    "KEY(id) VALUES (1, 'RUNNING', CURRENT_TIMESTAMP, 0, CURRENT_TIMESTAMP)"
                );
            }
            initialized = true;
        } catch (SQLException e) {
            System.err.println("Error initializing database: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Log a transaction message to the database
     */
    public void logTransaction(String transactionId, ISOMsg message, String direction) {
        LogEvent evt = new LogEvent(this, "db-log");
        try {
            if (!initialized) {
                initializeDatabase();
            }
            
            String mti = message.getMTI();
            String processingCode = message.getString(3);
            String amount = message.getString(4);
            String transmissionDateTime = message.getString(7);
            String stan = message.getString(11);
            String rrn = message.getString(37);
            String responseCode = message.getString(39);
            String terminalId = message.getString(41);
            String merchantId = message.getString(42);
            String rawMessage = formatRawMessage(message);
            
            try (Connection conn = getConnection()) {
                String sql = 
                    "INSERT INTO transactions " +
                    "(id, mti, processing_code, amount, transmission_datetime, stan, rrn, " +
                    "response_code, terminal_id, merchant_id, direction, raw_message, timestamp) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
                
                try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
                    pstmt.setString(1, transactionId);
                    pstmt.setString(2, mti);
                    pstmt.setString(3, processingCode);
                    pstmt.setString(4, amount);
                    pstmt.setString(5, transmissionDateTime);
                    pstmt.setString(6, stan);
                    pstmt.setString(7, rrn);
                    pstmt.setString(8, responseCode);
                    pstmt.setString(9, terminalId);
                    pstmt.setString(10, merchantId);
                    pstmt.setString(11, direction);
                    pstmt.setString(12, rawMessage);
                    pstmt.setTimestamp(13, new Timestamp(System.currentTimeMillis()));
                    
                    pstmt.executeUpdate();
                }
                
                // Update system status
                updateSystemStatus(conn);
            }
        } catch (Exception e) {
            evt.addMessage("Error logging transaction: " + e.getMessage());
        } finally {
            Logger.log(evt);
        }
    }

    /**
     * Update system status counters
     */
    private void updateSystemStatus(Connection conn) throws SQLException {
        String sql = 
            "UPDATE system_status " +
            "SET transactions_processed = transactions_processed + 1, " +
            "last_updated = CURRENT_TIMESTAMP " +
            "WHERE id = 1";
        
        try (Statement stmt = conn.createStatement()) {
            stmt.executeUpdate(sql);
        }
    }

    /**
     * Get system status information
     */
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        try {
            if (!initialized) {
                initializeDatabase();
            }
            
            try (Connection conn = getConnection()) {
                String sql = "SELECT * FROM system_status WHERE id = 1";
                
                try (Statement stmt = conn.createStatement();
                     ResultSet rs = stmt.executeQuery(sql)) {
                    if (rs.next()) {
                        status.put("status", rs.getString("status"));
                        status.put("startTime", rs.getTimestamp("start_time"));
                        status.put("transactionsProcessed", rs.getLong("transactions_processed"));
                        status.put("lastUpdated", rs.getTimestamp("last_updated"));
                    }
                }
            }
        } catch (SQLException e) {
            status.put("error", "Database error: " + e.getMessage());
        }
        return status;
    }

    /**
     * Get recent transactions from the database
     */
    public List<Map<String, Object>> getRecentTransactions(int limit) {
        List<Map<String, Object>> transactions = new ArrayList<>();
        try {
            if (!initialized) {
                initializeDatabase();
            }
            
            try (Connection conn = getConnection()) {
                String sql = 
                    "SELECT * FROM transactions " +
                    "ORDER BY timestamp DESC " +
                    "LIMIT ?";
                
                try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
                    pstmt.setInt(1, limit);
                    
                    try (ResultSet rs = pstmt.executeQuery()) {
                        while (rs.next()) {
                            Map<String, Object> txn = new HashMap<>();
                            txn.put("id", rs.getString("id"));
                            txn.put("mti", rs.getString("mti"));
                            txn.put("processingCode", rs.getString("processing_code"));
                            txn.put("amount", rs.getString("amount"));
                            txn.put("transmissionDateTime", rs.getString("transmission_datetime"));
                            txn.put("stan", rs.getString("stan"));
                            txn.put("rrn", rs.getString("rrn"));
                            txn.put("responseCode", rs.getString("response_code"));
                            txn.put("terminalId", rs.getString("terminal_id"));
                            txn.put("merchantId", rs.getString("merchant_id"));
                            txn.put("direction", rs.getString("direction"));
                            txn.put("rawMessage", rs.getString("raw_message"));
                            txn.put("timestamp", rs.getTimestamp("timestamp"));
                            transactions.add(txn);
                        }
                    }
                }
            }
        } catch (SQLException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Database error: " + e.getMessage());
            transactions.add(error);
        }
        return transactions;
    }

    /**
     * Get the transaction counts for the last 24 hours, grouped by hour
     */
    public Map<String, Integer> getTransactionCountsByHour() {
        Map<String, Integer> counts = new HashMap<>();
        try {
            if (!initialized) {
                initializeDatabase();
            }
            
            try (Connection conn = getConnection()) {
                String sql = 
                    "SELECT HOUR(timestamp) as hour, COUNT(*) as count " +
                    "FROM transactions " +
                    "WHERE timestamp > DATEADD('HOUR', -24, CURRENT_TIMESTAMP) " +
                    "GROUP BY HOUR(timestamp) " +
                    "ORDER BY hour";
                
                try (Statement stmt = conn.createStatement();
                     ResultSet rs = stmt.executeQuery(sql)) {
                    while (rs.next()) {
                        counts.put(String.valueOf(rs.getInt("hour")), rs.getInt("count"));
                    }
                }
            }
        } catch (SQLException e) {
            counts.put("error", -1);
        }
        return counts;
    }

    /**
     * Format an ISO message for logging as raw message
     */
    private String formatRawMessage(ISOMsg message) {
        StringBuilder sb = new StringBuilder();
        sb.append("MTI: ").append(message.getMTI()).append("\n");
        
        try {
            for (int i = 1; i <= 128; i++) {
                if (message.hasField(i)) {
                    String value = message.getString(i);
                    // Mask sensitive data (e.g., PAN, CVV)
                    if (i == 2) { // PAN
                        value = maskPan(value);
                    } else if (i == 35) { // Track 2
                        value = "MASKED-TRACK-DATA";
                    } else if (i == 52) { // PIN data
                        value = "MASKED-PIN-DATA";
                    }
                    sb.append("Field ").append(i).append(": ").append(value).append("\n");
                }
            }
        } catch (ISOException e) {
            sb.append("Error formatting message: ").append(e.getMessage());
        }
        
        return sb.toString();
    }

    /**
     * Mask a PAN for security
     */
    private String maskPan(String pan) {
        if (pan == null || pan.length() < 13) {
            return "MASKED-PAN";
        }
        
        return pan.substring(0, 6) + "******" + pan.substring(pan.length() - 4);
    }

    /**
     * Get a database connection
     */
    private Connection getConnection() throws SQLException {
        return DriverManager.getConnection(dbUrl, dbUser, dbPassword);
    }
}
