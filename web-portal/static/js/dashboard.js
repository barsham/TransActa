document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    fetchSystemStatus();
    fetchRecentTransactions();
    fetchTransactionStats();
    
    // Set up refresh interval (every 10 seconds)
    setInterval(function() {
        fetchSystemStatus();
        fetchRecentTransactions();
        fetchTransactionStats();
    }, 10000);
});

/**
 * Fetch system status from the API
 */
function fetchSystemStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateSystemStatusDisplay(data);
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            document.getElementById('system-status').innerHTML = 
                '<div class="alert alert-danger">Error loading system status</div>';
        });
}

/**
 * Fetch recent transactions from the API
 */
function fetchRecentTransactions() {
    fetch('/api/transactions?limit=5')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateRecentTransactionsDisplay(data);
        })
        .catch(error => {
            console.error('Error fetching recent transactions:', error);
            document.getElementById('recent-transactions').innerHTML = 
                '<div class="alert alert-danger">Error loading recent transactions</div>';
        });
}

/**
 * Fetch transaction statistics from the API
 */
function fetchTransactionStats() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateTransactionStatsChart(data);
        })
        .catch(error => {
            console.error('Error fetching transaction stats:', error);
            document.getElementById('transaction-chart').innerHTML = 
                '<div class="alert alert-danger">Error loading transaction statistics</div>';
        });
}

/**
 * Update the system status display
 */
function updateSystemStatusDisplay(data) {
    const statusElement = document.getElementById('system-status');
    if (!statusElement) return;
    
    // Format timestamps
    const startTime = data.startTime ? new Date(data.startTime).toLocaleString() : 'N/A';
    const lastUpdated = data.lastUpdated ? new Date(data.lastUpdated).toLocaleString() : 'N/A';
    
    // Calculate uptime
    let uptime = 'N/A';
    if (data.startTime) {
        const startTimeMs = new Date(data.startTime).getTime();
        const now = new Date().getTime();
        const uptimeMs = now - startTimeMs;
        
        // Format uptime
        const seconds = Math.floor(uptimeMs / 1000) % 60;
        const minutes = Math.floor(uptimeMs / (1000 * 60)) % 60;
        const hours = Math.floor(uptimeMs / (1000 * 60 * 60)) % 24;
        const days = Math.floor(uptimeMs / (1000 * 60 * 60 * 24));
        
        uptime = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }
    
    // Determine status badge class
    let statusBadgeClass = 'bg-secondary';
    if (data.status === 'RUNNING') {
        statusBadgeClass = 'bg-success';
    } else if (data.status === 'ERROR' || data.status === 'STOPPED') {
        statusBadgeClass = 'bg-danger';
    } else if (data.status === 'WARNING') {
        statusBadgeClass = 'bg-warning';
    }
    
    // Build HTML content
    const html = `
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">System Status</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Status:</strong> <span class="badge ${statusBadgeClass}">${data.status || 'UNKNOWN'}</span></p>
                        <p><strong>Start Time:</strong> ${startTime}</p>
                        <p><strong>Uptime:</strong> ${uptime}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Transactions Processed:</strong> ${data.transactionsProcessed || 0}</p>
                        <p><strong>Last Updated:</strong> ${lastUpdated}</p>
                    </div>
                </div>
            </div>
            <div class="card-footer text-end">
                <a href="/system-status" class="btn btn-sm btn-primary">View Details</a>
            </div>
        </div>
    `;
    
    statusElement.innerHTML = html;
}

/**
 * Update the recent transactions display
 */
function updateRecentTransactionsDisplay(transactions) {
    const transactionsElement = document.getElementById('recent-transactions');
    if (!transactionsElement) return;
    
    if (!transactions || transactions.length === 0) {
        transactionsElement.innerHTML = '<div class="alert alert-info">No transactions available</div>';
        return;
    }
    
    // Build HTML for transactions table
    let tableHtml = `
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Recent Transactions</h5>
            </div>
            <div class="card-body p-0">
                <table class="table table-striped table-hover mb-0">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Amount</th>
                            <th>Response</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Add rows for each transaction
    transactions.forEach(txn => {
        // Format transaction data
        const amount = txn.amount ? formatAmount(txn.amount) : 'N/A';
        const time = txn.timestamp ? new Date(txn.timestamp).toLocaleTimeString() : 'N/A';
        const id = txn.id || 'Unknown';
        const type = getMessageTypeDescription(txn.mti) || 'Unknown';
        
        // Determine response badge class
        let responseBadgeClass = 'bg-secondary';
        let responseText = txn.responseCode || 'N/A';
        
        if (txn.responseCode === '00') {
            responseBadgeClass = 'bg-success';
            responseText = 'Approved';
        } else if (txn.responseCode) {
            responseBadgeClass = 'bg-danger';
            responseText = `Declined (${txn.responseCode})`;
        }
        
        // Add table row
        tableHtml += `
            <tr>
                <td><small>${id}</small></td>
                <td>${type}</td>
                <td>${amount}</td>
                <td><span class="badge ${responseBadgeClass}">${responseText}</span></td>
                <td>${time}</td>
            </tr>
        `;
    });
    
    // Close the table and add footer
    tableHtml += `
                    </tbody>
                </table>
            </div>
            <div class="card-footer text-end">
                <a href="/transactions" class="btn btn-sm btn-primary">View All Transactions</a>
            </div>
        </div>
    `;
    
    transactionsElement.innerHTML = tableHtml;
}

/**
 * Update the transaction statistics chart
 */
function updateTransactionStatsChart(data) {
    const chartElement = document.getElementById('transaction-chart');
    if (!chartElement) return;
    
    // Create chart container if it doesn't exist
    let canvasElement = document.getElementById('transactions-chart-canvas');
    if (!canvasElement) {
        chartElement.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Transaction Volume (Last 24 Hours)</h5>
                </div>
                <div class="card-body">
                    <canvas id="transactions-chart-canvas"></canvas>
                </div>
            </div>
        `;
        canvasElement = document.getElementById('transactions-chart-canvas');
    }
    
    // Prepare chart data
    const hours = [];
    const counts = [];
    
    // Generate all hours (0-23) with zero counts
    for (let i = 0; i < 24; i++) {
        hours.push(i.toString());
        counts.push(0);
    }
    
    // Update with actual counts from data
    if (data) {
        Object.entries(data).forEach(([hour, count]) => {
            if (!isNaN(parseInt(hour)) && parseInt(hour) >= 0 && parseInt(hour) < 24) {
                counts[parseInt(hour)] = count;
            }
        });
    }
    
    // Create or update the chart
    if (window.transactionChart) {
        window.transactionChart.data.datasets[0].data = counts;
        window.transactionChart.update();
    } else {
        window.transactionChart = new Chart(canvasElement, {
            type: 'bar',
            data: {
                labels: hours.map(h => `${h}:00`),
                datasets: [{
                    label: 'Transactions',
                    data: counts,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}

/**
 * Format currency amount from ISO 8583 format
 */
function formatAmount(amount) {
    if (!amount) return 'N/A';
    
    // Convert to number and divide by 100 to get decimal places
    const numericAmount = parseInt(amount) / 100;
    
    // Format with currency symbol and decimal places
    return numericAmount.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD'
    });
}

/**
 * Get a description for a message type indicator (MTI)
 */
function getMessageTypeDescription(mti) {
    if (!mti) return 'Unknown';
    
    // First digit - version
    const version = mti.charAt(0);
    
    // Second digit - message class
    const messageClass = mti.charAt(1);
    let classDesc = '';
    
    switch (messageClass) {
        case '0': classDesc = 'Authorization'; break;
        case '1': classDesc = 'Response'; break;
        case '2': classDesc = 'Financial'; break;
        case '3': classDesc = 'File Action'; break;
        case '4': classDesc = 'Reversal'; break;
        case '5': classDesc = 'Reconciliation'; break;
        case '6': classDesc = 'Administrative'; break;
        case '7': classDesc = 'Fee Collection'; break;
        case '8': classDesc = 'Network Management'; break;
        default: classDesc = 'Unknown'; break;
    }
    
    return classDesc;
}
