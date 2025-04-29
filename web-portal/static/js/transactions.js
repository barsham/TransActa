/**
 * Transactions page JavaScript for SillyPostilion Web Portal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables for pagination
    let currentPage = 1;
    const defaultLimit = 50;
    let totalPages = 1;
    
    // Set up event listeners
    document.getElementById('refresh-transactions').addEventListener('click', function() {
        fetchTransactions();
    });
    
    document.getElementById('transaction-limit').addEventListener('change', function() {
        fetchTransactions();
    });
    
    document.getElementById('apply-filters').addEventListener('click', function() {
        fetchTransactions();
    });
    
    // Initial load of transactions
    fetchTransactions();
    
    // Set up refresh interval
    setInterval(fetchTransactions, 30000);  // Refresh every 30 seconds
    
    /**
     * Fetch transactions from the API
     */
    function fetchTransactions(page = 1) {
        currentPage = page;
        
        // Show loading state
        document.getElementById('loading-transactions').style.display = 'block';
        document.getElementById('empty-transactions').style.display = 'none';
        document.getElementById('transactions-table-container').style.display = 'none';
        
        // Get filters
        const limit = document.getElementById('transaction-limit').value;
        const mtiFilter = document.getElementById('filter-mti').value;
        const responseFilter = document.getElementById('filter-response').value;
        const dateFilter = document.getElementById('filter-date').value;
        const searchTerm = document.getElementById('search-term').value.trim();
        
        // Build query parameters
        let params = new URLSearchParams();
        params.append('limit', limit);
        params.append('page', currentPage);
        
        if (mtiFilter) params.append('mti', mtiFilter);
        if (responseFilter) params.append('response', responseFilter);
        if (dateFilter) params.append('date', dateFilter);
        if (searchTerm) params.append('search', searchTerm);
        
        // Fetch transactions with filters
        fetch(`/api/transactions?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                displayTransactions(data);
            })
            .catch(error => {
                console.error('Error fetching transactions:', error);
                document.getElementById('loading-transactions').style.display = 'none';
                document.getElementById('empty-transactions').style.display = 'block';
            });
    }
    
    /**
     * Display transactions in the table
     */
    function displayTransactions(data) {
        document.getElementById('loading-transactions').style.display = 'none';
        
        let transactions = [];
        let metadata = {};
        
        // If data is an array, it's just transactions without metadata
        if (Array.isArray(data)) {
            transactions = data;
            totalPages = 1;
        } else if (data && typeof data === 'object') {
            // If data has transactions and metadata properties
            transactions = data.transactions || [];
            metadata = data.metadata || {};
            totalPages = metadata.totalPages || 1;
        }
        
        // Show empty state if no transactions
        if (!transactions || transactions.length === 0) {
            document.getElementById('empty-transactions').style.display = 'block';
            return;
        }
        
        // Create table rows for transactions
        const tableBody = document.getElementById('transactions-table-body');
        tableBody.innerHTML = '';
        
        transactions.forEach(txn => {
            const row = document.createElement('tr');
            
            // Determine the transaction type icon and class
            let mtiType = 'financial';
            let mtiIcon = 'financial.svg';
            
            if (txn.mti) {
                const mtiFirstTwo = txn.mti.substring(0, 2);
                if (mtiFirstTwo === '01') {
                    mtiType = 'auth';
                    mtiIcon = 'auth.svg';
                } else if (mtiFirstTwo === '04') {
                    mtiType = 'reversal';
                    mtiIcon = 'reversal.svg';
                } else if (mtiFirstTwo === '08') {
                    mtiType = 'network';
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
        
        // Show the transactions table
        document.getElementById('transactions-table-container').style.display = 'block';
        
        // Update pagination
        updatePagination(totalPages, currentPage);
    }
    
    /**
     * Update pagination controls
     */
    function updatePagination(totalPages, currentPage) {
        const paginationElement = document.getElementById('transaction-pagination');
        if (!paginationElement) return;
        
        const paginationList = paginationElement.querySelector('ul');
        paginationList.innerHTML = '';
        
        // Previous button
        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevItem.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous" 
               ${currentPage > 1 ? `onclick="fetchTransactions(${currentPage - 1}); return false;"` : ''}>
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        paginationList.appendChild(prevItem);
        
        // Page numbers
        const maxPages = 5; // Maximum number of page links to show
        let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
        let endPage = Math.min(totalPages, startPage + maxPages - 1);
        
        // Adjust if we're near the end
        if (endPage - startPage + 1 < maxPages && startPage > 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageItem.innerHTML = `
                <a class="page-link" href="#" 
                   ${i !== currentPage ? `onclick="fetchTransactions(${i}); return false;"` : ''}>
                    ${i}
                </a>
            `;
            paginationList.appendChild(pageItem);
        }
        
        // Next button
        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextItem.innerHTML = `
            <a class="page-link" href="#" aria-label="Next" 
               ${currentPage < totalPages ? `onclick="fetchTransactions(${currentPage + 1}); return false;"` : ''}>
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        paginationList.appendChild(nextItem);
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
});

/**
 * Show transaction details in a modal (global function)
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
 * Format amount (global function for use in the onclick handler)
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
 * Get a description for a response code (global function)
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
