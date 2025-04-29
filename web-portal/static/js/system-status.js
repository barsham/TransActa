/**
 * System Status page JavaScript for SillyPostilion Web Portal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadSystemStatus();
    loadTransactionMetrics();
    loadSystemLogs();
    initTransactionVolumeChart();
    
    // Set up refresh buttons
    document.getElementById('refresh-status').addEventListener('click', function() {
        loadSystemStatus();
    });
    
    document.getElementById('refresh-logs').addEventListener('click', function() {
        loadSystemLogs();
    });
    
    // Set up refresh intervals
    setInterval(loadSystemStatus, 10000); // Every 10 seconds
    setInterval(loadTransactionMetrics, 15000); // Every 15 seconds
    setInterval(loadSystemLogs, 30000); // Every 30 seconds
    setInterval(initTransactionVolumeChart, 60000); // Every minute
});

/**
 * Load system status information
 */
function loadSystemStatus() {
    const loadingElement = document.getElementById('loading-system-status');
    const emptyElement = document.getElementById('empty-system-status');
    
    loadingElement.style.display = 'block';
    emptyElement.style.display = 'none';
    
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            loadingElement.style.display = 'none';
            updateSystemOverview(data);
            updateSystemHealth(data);
            updateSidebarStatus(data);
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            loadingElement.style.display = 'none';
            emptyElement.style.display = 'block';
            
            // Update navbar status to offline
            document.getElementById('navbar-status-indicator').innerHTML = 
                '<span class="badge rounded-pill bg-danger">Offline</span>';
        });
}

/**
 * Load transaction metrics
 */
function loadTransactionMetrics() {
    fetch('/api/transactions?limit=500')
        .then(response => response.json())
        .then(data => {
            // Count transactions by type
            let authCount = 0;
            let financialCount = 0;
            let reversalCount = 0;
            let networkCount = 0;
            
            data.forEach(txn => {
                if (txn.mti) {
                    const mtiFirstTwo = txn.mti.substring(0, 2);
                    if (mtiFirstTwo === '01') {
                        authCount++;
                    } else if (mtiFirstTwo === '02') {
                        financialCount++;
                    } else if (mtiFirstTwo === '04') {
                        reversalCount++;
                    } else if (mtiFirstTwo === '08') {
                        networkCount++;
                    }
                }
            });
            
            // Calculate total for percentages
            const total = authCount + financialCount + reversalCount + networkCount;
            
            // Update counts
            document.getElementById('auth-count').textContent = authCount;
            document.getElementById('financial-count').textContent = financialCount;
            document.getElementById('reversal-count').textContent = reversalCount;
            document.getElementById('network-count').textContent = networkCount;
            
            // Update progress bars
            if (total > 0) {
                updateProgressBar('auth-progress', (authCount / total) * 100);
                updateProgressBar('financial-progress', (financialCount / total) * 100);
                updateProgressBar('reversal-progress', (reversalCount / total) * 100);
                updateProgressBar('network-progress', (networkCount / total) * 100);
            }
        })
        .catch(error => {
            console.error('Error fetching transaction metrics:', error);
        });
}

/**
 * Update a progress bar element
 */
function updateProgressBar(elementId, percentage) {
    const progressBar = document.getElementById(elementId);
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
}

/**
 * Update the system overview section
 */
function updateSystemOverview(data) {
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
    
    // Build overview HTML
    const overviewHtml = `
        <div class="row">
            <div class="col-md-6">
                <h4><span class="badge ${statusBadgeClass}">${data.status || 'UNKNOWN'}</span></h4>
                <p class="mb-1"><strong>Start Time:</strong> ${startTime}</p>
                <p class="mb-1"><strong>Uptime:</strong> ${uptime}</p>
                <p class="mb-1"><strong>Last Updated:</strong> ${lastUpdated}</p>
            </div>
            <div class="col-md-6">
                <div class="d-flex align-items-center justify-content-center h-100">
                    <div class="text-center">
                        <h2 class="display-4">${data.transactionsProcessed || 0}</h2>
                        <p class="text-muted">Transactions Processed</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('system-overview').innerHTML = overviewHtml;
}

/**
 * Update the system health section
 */
function updateSystemHealth(data) {
    // System health metrics
    const isHealthy = data.status === 'RUNNING';
    const memoryUsage = Math.floor(Math.random() * 40) + 30; // Simulated memory usage (30-70%)
    const cpuUsage = Math.floor(Math.random() * 30) + 10; // Simulated CPU usage (10-40%)
    const responseTime = Math.floor(Math.random() * 100) + 10; // Simulated response time (10-110ms)
    
    // Build health HTML
    const healthHtml = `
        <div class="row mb-4">
            <div class="col-sm-6 col-md-4 text-center">
                <h5>CPU Usage</h5>
                <div class="progress mb-2" style="height: 20px;">
                    <div class="progress-bar ${cpuUsage > 80 ? 'bg-danger' : cpuUsage > 60 ? 'bg-warning' : 'bg-success'}" 
                         role="progressbar" style="width: ${cpuUsage}%;" 
                         aria-valuenow="${cpuUsage}" aria-valuemin="0" aria-valuemax="100">
                        ${cpuUsage}%
                    </div>
                </div>
            </div>
            <div class="col-sm-6 col-md-4 text-center">
                <h5>Memory Usage</h5>
                <div class="progress mb-2" style="height: 20px;">
                    <div class="progress-bar ${memoryUsage > 80 ? 'bg-danger' : memoryUsage > 60 ? 'bg-warning' : 'bg-success'}" 
                         role="progressbar" style="width: ${memoryUsage}%;" 
                         aria-valuenow="${memoryUsage}" aria-valuemin="0" aria-valuemax="100">
                        ${memoryUsage}%
                    </div>
                </div>
            </div>
            <div class="col-sm-6 col-md-4 text-center">
                <h5>Response Time</h5>
                <div class="progress mb-2" style="height: 20px;">
                    <div class="progress-bar ${responseTime > 100 ? 'bg-danger' : responseTime > 50 ? 'bg-warning' : 'bg-success'}" 
                         role="progressbar" style="width: ${Math.min(responseTime, 100)}%;" 
                         aria-valuenow="${responseTime}" aria-valuemin="0" aria-valuemax="100">
                        ${responseTime}ms
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <h5>System Checks</h5>
                <table class="table">
                    <tr>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> Transaction Processor</td>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> Database Connection</td>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> API Server</td>
                    </tr>
                    <tr>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> Message Queue</td>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> ISO Channel</td>
                        <td><i class="fas fa-${isHealthy ? 'check text-success' : 'times text-danger'}"></i> Logging System</td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    document.getElementById('system-health').innerHTML = healthHtml;
}

/**
 * Update sidebar status indicator
 */
function updateSidebarStatus(data) {
    // Update navbar status indicator
    let statusClass = 'bg-success';
    let statusText = 'Online';
    
    if (data.status !== 'RUNNING') {
        statusClass = data.status === 'WARNING' ? 'bg-warning' : 'bg-danger';
        statusText = data.status === 'WARNING' ? 'Warning' : 'Offline';
    }
    
    document.getElementById('navbar-status-indicator').innerHTML = 
        `<span class="badge rounded-pill ${statusClass}">${statusText}</span>`;
    
    // Update sidebar status indicator
    const sidebarStatus = document.getElementById('sidebar-status-indicator');
    if (sidebarStatus) {
        let statusIndicatorClass = 'online';
        let statusIndicatorText = 'Online';
        
        if (data.status !== 'RUNNING') {
            statusIndicatorClass = data.status === 'WARNING' ? 'warning' : 'offline';
            statusIndicatorText = data.status === 'WARNING' ? 'Warning' : 'Offline';
        }
        
        sidebarStatus.innerHTML = `
            <span class="system-status-indicator ${statusIndicatorClass}"></span>
            ${statusIndicatorText}
        `;
    }
}

/**
 * Load system logs
 */
function loadSystemLogs() {
    // Simulate system logs - in a real system, these would come from an API
    const now = new Date();
    const logs = [
        {time: new Date(now - 1000 * 60 * 2), status: 'INFO', message: 'System status check completed'},
        {time: new Date(now - 1000 * 60 * 15), status: 'INFO', message: 'Processed transaction batch #12345'},
        {time: new Date(now - 1000 * 60 * 30), status: 'INFO', message: 'API server processed 50 requests'},
        {time: new Date(now - 1000 * 60 * 45), status: 'WARNING', message: 'High response time detected'},
        {time: new Date(now - 1000 * 60 * 60), status: 'INFO', message: 'Database cleanup completed'},
        {time: new Date(now - 1000 * 60 * 120), status: 'INFO', message: 'System started successfully'}
    ];
    
    // Build logs HTML
    let logsHtml = '';
    logs.forEach(log => {
        const timeStr = log.time.toLocaleTimeString();
        let statusClass = 'bg-info';
        
        if (log.status === 'ERROR') {
            statusClass = 'bg-danger';
        } else if (log.status === 'WARNING') {
            statusClass = 'bg-warning';
        } else if (log.status === 'SUCCESS') {
            statusClass = 'bg-success';
        }
        
        logsHtml += `
            <tr>
                <td>${timeStr}</td>
                <td><span class="badge ${statusClass}">${log.status}</span></td>
                <td>${log.message}</td>
            </tr>
        `;
    });
    
    document.getElementById('system-logs').innerHTML = logsHtml;
}

/**
 * Initialize or update the transaction volume chart
 */
function initTransactionVolumeChart() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
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
            
            // Get canvas context
            const ctx = document.getElementById('hourly-transaction-chart').getContext('2d');
            
            // Check if chart already exists
            const chartInstance = Chart.getChart(ctx);
            if (chartInstance) {
                // Update existing chart
                chartInstance.data.labels = hours.map(h => `${h}:00`);
                chartInstance.data.datasets[0].data = counts;
                chartInstance.update();
            } else {
                // Create new chart
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: hours.map(h => `${h}:00`),
                        datasets: [{
                            label: 'Transactions',
                            data: counts,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 2,
                            pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                            tension: 0.4,
                            fill: true
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
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Transaction Volume by Hour'
                            },
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error fetching transaction stats:', error);
        });
}
