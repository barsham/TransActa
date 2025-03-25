from datetime import datetime
from app import db

class Transaction(db.Model):
    """
    Model for storing transaction data fetched from the Java backend
    This is used for caching data from the transaction processor
    """
    id = db.Column(db.String(50), primary_key=True)
    mti = db.Column(db.String(4))
    processing_code = db.Column(db.String(6))
    amount = db.Column(db.String(12))
    transmission_datetime = db.Column(db.String(10))
    stan = db.Column(db.String(6))
    rrn = db.Column(db.String(12))
    response_code = db.Column(db.String(2))
    terminal_id = db.Column(db.String(8))
    merchant_id = db.Column(db.String(15))
    direction = db.Column(db.String(10))
    raw_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Transaction {self.id}>"
    
    def to_dict(self):
        """Convert transaction to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'mti': self.mti,
            'processingCode': self.processing_code,
            'amount': self.amount,
            'transmissionDatetime': self.transmission_datetime,
            'stan': self.stan,
            'rrn': self.rrn,
            'responseCode': self.response_code,
            'terminalId': self.terminal_id,
            'merchantId': self.merchant_id,
            'direction': self.direction,
            'rawMessage': self.raw_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class SystemStatus(db.Model):
    """
    Model for storing system status information
    This is used for caching data from the transaction processor
    """
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20))
    start_time = db.Column(db.DateTime)
    transactions_processed = db.Column(db.BigInteger)
    last_updated = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<SystemStatus {self.status}>"
    
    def to_dict(self):
        """Convert system status to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'status': self.status,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'transactionsProcessed': self.transactions_processed,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None
        }
