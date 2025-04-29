/**
 * Dashboard-specific JavaScript for SillyPostilion Web Portal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fetch all required data on page load
    fetchSystemStatus();
    fetchRecentTransactions();
    fetchTransactionStats();
    
    // Set up refresh intervals
    setInterval(fetchSystemStatus, 10000);  // Update status every 10 seconds
    setInterval(fetchRecentTransactions, 15000);  // Update transactions every 15 seconds
    setInterval(fetchTransactionStats, 30000);  // Update stats every 30 seconds
});

/**
 * Fetch system status from the API
 */
function fetchSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => updateSystemStatusDisplay(data))
        .catch(error => {
            console.error('Error fetching system status:', error);
            // Update navbar status to offline
            document.getElementById('navbar-status-indicator').innerHTML = 
                '<span class="badge rounded-pill bg-danger">Offline</span>';
        });
}

/**
 * Fetch recent transactions from the API
 */
function fetchRecentTransactions() {
    document.getElementById('loading-transactions').style.display = 'block';
    document.getElementById('empty-transactions').style.display = 'none';
    document.getElementById('transactions-table-container').style.display = 'none';
    
    fetch('/api/transactions?limit=5')
        .then(response => response.json())
        .then(data => updateRecentTransactionsDisplay(data))
        .catch(error => {
            console.error('Error fetching transactions:', error);
            document.getElementById('loading-transactions').style.display = 'none';
            document.getElementById('empty-transactions').style.display = 'block';
        });
}

/**
 * Fetch transaction statistics from the API
 */
function fetchTransactionStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => updateTransactionStatsChart(data))
        .catch(error => {
            console.error('Error fetching transaction stats:', error);
        });
}

/**
 * Update the system status display
 */
function updateSystemStatusDisplay(data) {
    // Update navbar status indicator
    let statusClass = 'bg-success';
    let statusText = 'Online';
    
    if (data.status !== 'RUNNING') {
        statusClass = data.status === 'WARNING' ? 'bg-warning' : 'bg-danger';
        statusText = data.status === 'WARNING' ? 'Warning' : 'Offline';
    }
    
    document.getElementById('navbar-status-indicator').innerHTML = 
        `<span class="badge rounded-pill ${statusClass}">${statusText}</span>`;
    
    // Build system status card content
    const startTime = data.startTime ? new Date(data.startTime).toLocaleString() : 'N/A';
    const statusHtml = `
        <div class="row">
            <div class="col-md-6">
                <h3><span class="badge ${statusClass}">${data.status || 'UNKNOWN'}</span></h3>
                <p class="mb-1"><strong>Start Time:</strong> ${startTime}</p>
                <p class="mb-1"><strong>Transactions Processed:</strong> ${data.transactionsProcessed || 0}</p>
            </div>
            <div class="col-md-6 d-flex align-items-center justify-content-center">
                <div class="text-center">
                    <div class="system-status-indicator ${statusText.toLowerCase()}"></div>
                    <p class="text-muted mb-0">System Status</p>
                </div>
            </div>
        </div>
    `;
    
    // Update the system status container
    const statusContainer = document.getElementById('system-status');
    if (statusContainer) {
        const cardBody = statusContainer.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = statusHtml;
        }
    }
}

/**
 * Update the recent transactions display
 */
function updateRecentTransactionsDisplay(transactions) {
    document.getElementById('loading-transactions').style.display = 'none';
    
    if (!transactions || transactions.length === 0) {
        document.getElementById('empty-transactions').style.display = 'block';
        return;
    }
    
    // Create table rows for each transaction
    const tableBody = document.createElement('tbody');
    
    transactions.forEach(txn => {
        const row = document.createElement('tr');
        
        // Determine the transaction type icon and class
        let mtiType = 'financial';
        let mtiClass = 'primary';
        let mtiIcon = 'financial.svg';
        
        if (txn.mti) {
            const mtiFirstTwo = txn.mti.substring(0, 2);
            if (mtiFirstTwo === '01') {
                mtiType = 'auth';
                mtiClass = 'secondary';
                mtiIcon = 'auth.svg';
            } else if (mtiFirstTwo === '04') {
                mtiType = 'reversal';
                mtiClass = 'danger';
                mtiIcon = 'reversal.svg';
            } else if (mtiFirstTwo === '08') {
                mtiType = 'network';
                mtiClass = 'info';
                mtiIcon = 'network.svg';
            }
        }
        
        // Determine status badge color
        let statusClass = 'secondary';
        let statusText = 'Unknown';
        
        if (txn.responseCode) {
            if (txn.responseCode === '00') {
                statusClass = 'success';
                statusText = 'Approved';
            } else {
                statusClass = 'danger';
                statusText = 'Declined';
            }
        }
        
        // Format the timestamp
        const timestamp = txn.transmissionDatetime ? 
            new Date(txn.transmissionDatetime).toLocaleString() : 'Unknown';
        
        // Build the row HTML
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <img src="/static/images/${mtiIcon}" alt="${mtiType}" class="transaction-icon" style="width: 30px; height: 30px;">
                    <span class="badge-mti ${mtiType}">${txn.mti || '----'}</span>
                </div>
            </td>
            <td>${txn.id || '---'}</td>
            <td>${timestamp}</td>
            <td>${formatAmount(txn.amount) || '0.00'}</td>
            <td>${txn.terminalId || '----'}</td>
            <td><span class="badge bg-${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="showTransactionDetails('${txn.id}')">
                    <i class="fas fa-info-circle"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Create the table and add it to the container
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';
    
    const tableHead = document.createElement('thead');
    tableHead.innerHTML = `
        <tr>
            <th>Type</th>
            <th>Transaction ID</th>
            <th>Time</th>
            <th>Amount</th>
            <th>Terminal ID</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    `;
    
    table.appendChild(tableHead);
    table.appendChild(tableBody);
    
    // Update the transactions container
    const container = document.getElementById('transactions-table-container');
    container.innerHTML = '';
    container.appendChild(table);
    container.style.display = 'block';
}

/**
 * Update the transaction statistics chart
 */
function updateTransactionStatsChart(data) {
    const chartContainer = document.getElementById('transaction-chart');
    if (!chartContainer) return;
    
    const chartCanvas = chartContainer.querySelector('canvas');
    if (!chartCanvas) return;
    
    // Prepare data for Chart.js
    const labels = [];
    const values = [];
    
    // If data is available, process it
    if (data && Object.keys(data).length > 0) {
        // Sort hours to ensure they're in chronological order
        const sortedHours = Object.keys(data).sort((a, b) => parseInt(a) - parseInt(b));
        
        sortedHours.forEach(hour => {
            labels.push(`${hour}:00`);
            values.push(data[hour]);
        });
    } else {
        // Default data for empty state
        for (let i = 0; i < 24; i++) {
            labels.push(`${i}:00`);
            values.push(0);
        }
    }
    
    // Check if we already have a chart instance
    const chartInstance = Chart.getChart(chartCanvas);
    if (chartInstance) {
        // Update existing chart
        chartInstance.data.labels = labels;
        chartInstance.data.datasets[0].data = values;
        chartInstance.update();
    } else {
        // Create new chart
        new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Transactions',
                    data: values,
                    backgroundColor: 'rgba(74, 111, 165, 0.2)',
                    borderColor: 'rgba(74, 111, 165, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} transactions`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Update the loading state
    const loadingElem = chartContainer.querySelector('.text-center');
    if (loadingElem) {
        loadingElem.style.display = 'none';
    }
}

/**
 * Format currency amount from ISO 8583 format
 */
function formatAmount(amount) {
    if (!amount) return "0.00";
    
    // Convert to string and ensure it's at least 3 characters
    let amountStr = amount.toString();
    while (amountStr.length < 3) {
        amountStr = "0" + amountStr;
    }
    
    // Insert decimal point 2 places from the right
    const decimalPos = amountStr.length - 2;
    const formattedAmount = amountStr.substring(0, decimalPos) + "." + amountStr.substring(decimalPos);
    
    // Format with thousand separators and return
    return parseFloat(formattedAmount).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Show transaction details in a modal
 */
function showTransactionDetails(transactionId) {
    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    const modalBody = document.getElementById('transactionModalBody');
    
    // Show loading indicator
    modalBody.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border" role="status"></div>
            <p class="mt-2">Loading transaction details...</p>
        </div>
    `;
    
    modal.show();
    
    // Fetch transaction details
    fetch(`/api/transactions/${transactionId}`)
        .then(response => response.json())
        .then(transaction => {
            // Determine transaction type and icon
            let mtiType = 'Financial';
            let mtiIcon = 'financial.svg';
            
            if (transaction.mti) {
                const mtiFirstTwo = transaction.mti.substring(0, 2);
                if (mtiFirstTwo === '01') {
                    mtiType = 'Authorization';
                    mtiIcon = 'auth.svg';
                } else if (mtiFirstTwo === '04') {
                    mtiType = 'Reversal';
                    mtiIcon = 'reversal.svg';
                } else if (mtiFirstTwo === '08') {
                    mtiType = 'Network Management';
                    mtiIcon = 'network.svg';
                }
            }
            
            // Build modal content
            const timestamp = transaction.transmissionDatetime ? 
                new Date(transaction.transmissionDatetime).toLocaleString() : 'Unknown';
            
            const modalContent = `
                <div class="transaction-details">
                    <div class="row mb-4">
                        <div class="col-md-2 text-center">
                            <img src="/static/images/${mtiIcon}" alt="${mtiType}" class="img-fluid mb-2" style="max-width: 64px;">
                        </div>
                        <div class="col-md-10">
                            <h4>${mtiType} Transaction <span class="badge-mti ${mtiType.toLowerCase()}">${transaction.mti || '----'}</span></h4>
                            <p class="text-muted mb-0">Transaction ID: ${transaction.id || '---'}</p>
                            <p class="text-muted mb-0">Time: ${timestamp}</p>
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h5>Transaction Details</h5>
                            <table class="table table-sm">
                                <tr>
                                    <th width="40%">Amount</th>
                                    <td>${formatAmount(transaction.amount) || '0.00'}</td>
                                </tr>
                                <tr>
                                    <th>Processing Code</th>
                                    <td>${transaction.processingCode || '------'}</td>
                                </tr>
                                <tr>
                                    <th>Response Code</th>
                                    <td>
                                        <span class="badge bg-${transaction.responseCode === '00' ? 'success' : 'danger'}">
                                            ${transaction.responseCode || '--'}
                                        </span>
                                        ${getResponseCodeDescription(transaction.responseCode)}
                                    </td>
                                </tr>
                                <tr>
                                    <th>STAN</th>
                                    <td>${transaction.stan || '------'}</td>
                                </tr>
                                <tr>
                                    <th>RRN</th>
                                    <td>${transaction.rrn || '------------'}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div class="col-md-6">
                            <h5>Terminal Information</h5>
                            <table class="table table-sm">
                                <tr>
                                    <th width="40%">Terminal ID</th>
                                    <td>${transaction.terminalId || '--------'}</td>
                                </tr>
                                <tr>
                                    <th>Merchant ID</th>
                                    <td>${transaction.merchantId || '------------'}</td>
                                </tr>
                                <tr>
                                    <th>Direction</th>
                                    <td>${transaction.direction || '------'}</td>
                                </tr>
                                <tr>
                                    <th>Timestamp</th>
                                    <td>${new Date(transaction.timestamp).toLocaleString()}</td>
                                </tr>
                                <tr>
                                    <th>Access Count</th>
                                    <td>${transaction.accessCount || '0'}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <h5>Raw Message</h5>
                            <pre class="bg-dark text-light p-3 rounded"><code>${transaction.rawMessage || 'No raw message available'}</code></pre>
                        </div>
                    </div>
                </div>
            `;
            
            modalBody.innerHTML = modalContent;
        })
        .catch(error => {
            console.error('Error fetching transaction details:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error loading transaction details. Please try again later.
                </div>
            `;
        });
}

/**
 * Get a description for a response code
 */
function getResponseCodeDescription(code) {
    const descriptions = {
        '00': 'Approved or completed successfully',
        '01': 'Refer to card issuer',
        '05': 'Do not honor',
        '14': 'Invalid card number',
        '51': 'Insufficient funds',
        '54': 'Expired card',
        '91': 'Issuer or switch inoperative',
        '96': 'System malfunction'
    };
    
    return descriptions[code] ? `(${descriptions[code]})` : '';
}

/**
 * Get a description for a message type indicator (MTI)
 */
function getMessageTypeDescription(mti) {
    if (!mti) return 'Unknown';
    
    const firstTwo = mti.substring(0, 2);
    const lastTwo = mti.substring(2, 4);
    
    let type = 'Unknown';
    switch (firstTwo) {
        case '01': type = 'Authorization'; break;
        case '02': type = 'Financial'; break;
        case '04': type = 'Reversal'; break;
        case '08': type = 'Network Management'; break;
    }
    
    let direction = 'Unknown';
    switch (lastTwo) {
        case '00': direction = 'Request'; break;
        case '10': direction = 'Response'; break;
        case '20': direction = 'Advice'; break;
        case '30': direction = 'Advice Response'; break;
    }
    
    return `${type} ${direction}`;
}
