import requests
import logging
from datetime import datetime
from flask import render_template, jsonify, request
from models import Transaction, SystemStatus, db

# Configure logging
logger = logging.getLogger(__name__)

# Transaction processor API endpoint
TRANSACTION_PROCESSOR_API = "http://localhost:8000/api"

def register_routes(app):
    """Register all routes with the Flask app"""
    
    # Add a context processor to provide current_year to all templates
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year}
    
    @app.route('/')
    def index():
        """Render the dashboard page"""
        return render_template('index.html')
    
    @app.route('/transactions')
    def transactions():
        """Render the transactions page"""
        return render_template('transactions.html')
    
    @app.route('/system-status')
    def system_status():
        """Render the system status page"""
        return render_template('system_status.html')
    
    @app.route('/api/transactions')
    def get_transactions():
        """Get transaction data from the transaction processor"""
        limit = request.args.get('limit', 50, type=int)
        
        try:
            # Attempt to fetch from transaction processor
            response = requests.get(f"{TRANSACTION_PROCESSOR_API}/transactions?limit={limit}", timeout=5)
            
            if response.status_code == 200:
                transactions = response.json()
                
                # Update the local cache
                update_transaction_cache(transactions)
                
                return jsonify(transactions)
            else:
                logger.warning(f"Failed to get transactions from processor: {response.status_code}")
                # Fall back to cached data
                cached_transactions = get_cached_transactions(limit)
                return jsonify(cached_transactions)
        
        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            # Fall back to cached data
            cached_transactions = get_cached_transactions(limit)
            return jsonify(cached_transactions)
    
    @app.route('/api/status')
    def get_status():
        """Get system status from the transaction processor"""
        try:
            # Attempt to fetch from transaction processor
            response = requests.get(f"{TRANSACTION_PROCESSOR_API}/status", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Update the local cache
                update_status_cache(status_data)
                
                return jsonify(status_data)
            else:
                logger.warning(f"Failed to get status from processor: {response.status_code}")
                # Fall back to cached data
                cached_status = get_cached_status()
                return jsonify(cached_status)
        
        except Exception as e:
            logger.error(f"Error fetching system status: {str(e)}")
            # Fall back to cached data
            cached_status = get_cached_status()
            return jsonify(cached_status)
    
    @app.route('/api/stats')
    def get_stats():
        """Get transaction statistics from the transaction processor"""
        try:
            # Attempt to fetch from transaction processor
            response = requests.get(f"{TRANSACTION_PROCESSOR_API}/stats", timeout=5)
            
            if response.status_code == 200:
                stats_data = response.json()
                return jsonify(stats_data)
            else:
                logger.warning(f"Failed to get stats from processor: {response.status_code}")
                # Return empty stats
                return jsonify({})
        
        except Exception as e:
            logger.error(f"Error fetching transaction stats: {str(e)}")
            # Return empty stats
            return jsonify({})


def update_transaction_cache(transactions):
    """Update the local cache with transaction data from the processor"""
    try:
        for txn_data in transactions:
            # Check if transaction exists in cache
            txn = Transaction.query.get(txn_data.get('id'))
            
            if txn is None:
                # Create new transaction in cache
                txn = Transaction(
                    id=txn_data.get('id'),
                    mti=txn_data.get('mti'),
                    processing_code=txn_data.get('processingCode'),
                    amount=txn_data.get('amount'),
                    transmission_datetime=txn_data.get('transmissionDateTime'),
                    stan=txn_data.get('stan'),
                    rrn=txn_data.get('rrn'),
                    response_code=txn_data.get('responseCode'),
                    terminal_id=txn_data.get('terminalId'),
                    merchant_id=txn_data.get('merchantId'),
                    direction=txn_data.get('direction'),
                    raw_message=txn_data.get('rawMessage')
                )
                
                # Parse timestamp if available
                if 'timestamp' in txn_data and txn_data['timestamp']:
                    try:
                        txn.timestamp = datetime.fromisoformat(txn_data['timestamp'].replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                db.session.add(txn)
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Error updating transaction cache: {str(e)}")
        db.session.rollback()


def update_status_cache(status_data):
    """Update the local cache with system status data from the processor"""
    try:
        # Get or create status record
        status = SystemStatus.query.get(1)
        
        if status is None:
            status = SystemStatus(id=1)
            db.session.add(status)
        
        # Update fields
        status.status = status_data.get('status')
        status.transactions_processed = status_data.get('transactionsProcessed', 0)
        
        # Parse timestamps if available
        if 'startTime' in status_data and status_data['startTime']:
            try:
                status.start_time = datetime.fromisoformat(status_data['startTime'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if 'lastUpdated' in status_data and status_data['lastUpdated']:
            try:
                status.last_updated = datetime.fromisoformat(status_data['lastUpdated'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Error updating status cache: {str(e)}")
        db.session.rollback()


def get_cached_transactions(limit):
    """Get cached transaction data"""
    try:
        transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        return [txn.to_dict() for txn in transactions]
    except Exception as e:
        logger.error(f"Error getting cached transactions: {str(e)}")
        return []


def get_cached_status():
    """Get cached system status"""
    try:
        status = SystemStatus.query.get(1)
        if status:
            return status.to_dict()
        else:
            # Return default status if not in cache
            return {
                'status': 'UNKNOWN',
                'startTime': None,
                'transactionsProcessed': 0,
                'lastUpdated': None
            }
    except Exception as e:
        logger.error(f"Error getting cached status: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'transactionsProcessed': 0
        }
