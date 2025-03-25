document.addEventListener('DOMContentLoaded', function() {
    // Initialize transactions page
    fetchTransactions();
    
    // Set up refresh button
    const refreshButton = document.getElementById('refresh-transactions');
    if (refreshButton) {
        refreshButton.addEventListener('click', fetchTransactions);
    }
    
    // Set up limit selector
    const limitSelect = document.getElementById('transaction-limit');
    if (limitSelect) {
        limitSelect.addEventListener('change', fetchTransactions);
    }
});

/**
 * Fetch transactions from the API
 */
function fetchTransactions() {
    // Show loading indicator
    const transactionsContainer = document.getElementById('transactions-container');
    if (transactionsContainer) {
        transactionsContainer.innerHTML = '<div class="text-center p-5"><div class="spinner-border" role="status"></div><p class="mt-2">Loading transactions...</p></div>';
    }
    
    // Get limit from select dropdown
    const limitSelect = document.getElementById('transaction-limit');
    const limit = limitSelect ? limitSelect.value : 50;
    
    // Fetch transactions
    fetch(`/api/transactions?limit=${limit}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayTransactions(data);
        })
        .catch(error => {
            console.error('Error fetching transactions:', error);
            if (transactionsContainer) {
                transactionsContainer.innerHTML = '<div class="alert alert-danger">Error loading transactions</div>';
            }
        });
}

/**
 * Display transactions in the page
 */
function displayTransactions(transactions) {
    const transactionsContainer = document.getElementById('transactions-container');
    if (!transactionsContainer) return;
    
    if (!transactions || transactions.length === 0) {
        transactionsContainer.innerHTML = '<div class="alert alert-info">No transactions available</div>';
        return;
    }
    
    // Build transactions table
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>MTI</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Terminal ID</th>
                        <th>Response</th>
                        <th>Time</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows for each transaction
    transactions.forEach(txn => {
        // Format transaction data
        const amount = txn.amount ? formatAmount(txn.amount) : 'N/A';
        const time = txn.timestamp ? new Date(txn.timestamp).toLocaleString() : 'N/A';
        const id = txn.id || 'Unknown';
        const mti = txn.mti || 'N/A';
        const type = getMessageTypeDescription(mti);
        const terminalId = txn.terminalId || 'N/A';
        
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
                <td>${mti}</td>
                <td>${type}</td>
                <td>${amount}</td>
                <td>${terminalId}</td>
                <td><span class="badge ${responseBadgeClass}">${responseText}</span></td>
                <td>${time}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-info" 
                        data-bs-toggle="modal" data-bs-target="#transactionModal"
                        onclick="showTransactionDetails('${id}', ${JSON.stringify(txn).replace(/"/g, '&quot;')})">
                        View
                    </button>
                </td>
            </tr>
        `;
    });
    
    // Close the table
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Update the container
    transactionsContainer.innerHTML = tableHtml;
}

/**
 * Show transaction details in a modal
 */
function showTransactionDetails(id, transaction) {
    // Update modal title
    const modalTitle = document.getElementById('transactionModalLabel');
    if (modalTitle) {
        modalTitle.textContent = `Transaction Details: ${id}`;
    }
    
    // Update modal body
    const modalBody = document.getElementById('transactionModalBody');
    if (modalBody) {
        // Format transaction data
        const mti = transaction.mti || 'N/A';
        const type = getMessageTypeDescription(mti);
        const amount = transaction.amount ? formatAmount(transaction.amount) : 'N/A';
        const processingCode = transaction.processingCode || 'N/A';
        const stan = transaction.stan || 'N/A';
        const rrn = transaction.rrn || 'N/A';
        const terminalId = transaction.terminalId || 'N/A';
        const merchantId = transaction.merchantId || 'N/A';
        const responseCode = transaction.responseCode || 'N/A';
        const transmissionDateTime = transaction.transmissionDateTime || 'N/A';
        const timestamp = transaction.timestamp ? new Date(transaction.timestamp).toLocaleString() : 'N/A';
        const direction = transaction.direction || 'N/A';
        
        // Format raw message
        const rawMessage = transaction.rawMessage || 'No raw message data available';
        
        // Build details HTML
        let detailsHtml = `
            <div class="row mb-3">
                <div class="col-md-6">
                    <h6>Basic Information</h6>
                    <table class="table table-sm">
                        <tr>
                            <th>MTI:</th>
                            <td>${mti}</td>
                        </tr>
                        <tr>
                            <th>Type:</th>
                            <td>${type}</td>
                        </tr>
                        <tr>
                            <th>Direction:</th>
                            <td>${direction}</td>
                        </tr>
                        <tr>
                            <th>Amount:</th>
                            <td>${amount}</td>
                        </tr>
                        <tr>
                            <th>Processing Code:</th>
                            <td>${processingCode}</td>
                        </tr>
                        <tr>
                            <th>Response Code:</th>
                            <td>${responseCode}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Transaction Details</h6>
                    <table class="table table-sm">
                        <tr>
                            <th>STAN:</th>
                            <td>${stan}</td>
                        </tr>
                        <tr>
                            <th>RRN:</th>
                            <td>${rrn}</td>
                        </tr>
                        <tr>
                            <th>Terminal ID:</th>
                            <td>${terminalId}</td>
                        </tr>
                        <tr>
                            <th>Merchant ID:</th>
                            <td>${merchantId}</td>
                        </tr>
                        <tr>
                            <th>Transmission Time:</th>
                            <td>${transmissionDateTime}</td>
                        </tr>
                        <tr>
                            <th>System Time:</th>
                            <td>${timestamp}</td>
                        </tr>
                    </table>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <h6>Raw Message</h6>
                    <pre class="bg-dark text-light p-3" style="max-height: 200px; overflow: auto;">${rawMessage}</pre>
                </div>
            </div>
        `;
        
        modalBody.innerHTML = detailsHtml;
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
    
    // Third and fourth digits - function
    const function1 = mti.charAt(2);
    const function2 = mti.charAt(3);
    
    if (messageClass === '0' || messageClass === '2') {
        // Authorization or Financial message
        if (function1 === '0' && function2 === '0') {
            return `${classDesc} Request`;
        } else if (function1 === '1' && function2 === '0') {
            return `${classDesc} Response`;
        }
    } else if (messageClass === '4') {
        // Reversal
        if (function1 === '0' && function2 === '0') {
            return 'Reversal Request';
        } else if (function1 === '1' && function2 === '0') {
            return 'Reversal Response';
        }
    } else if (messageClass === '8') {
        // Network Management
        if (function1 === '0' && function2 === '0') {
            return 'Network Management Request';
        } else if (function1 === '1' && function2 === '0') {
            return 'Network Management Response';
        }
    }
    
    return `${classDesc} (${mti})`;
}
