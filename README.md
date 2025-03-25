# SillyPostilion - Financial Transaction Processing System

![SillyPostilion Logo](generated-icon.png)

SillyPostilion is a robust financial transaction processing system based on TCP/IP and the AS2805 standard (Australian financial message protocol). The system is built using the industry-standard JPOS framework for reliable payment processing with a modern web monitoring portal.

## Overview

SillyPostilion consists of two main components:

1. **Transaction Processor** - A Java-based backend that handles financial transactions using the JPOS framework and AS2805 message format
2. **Web Portal** - A Python Flask-based frontend for real-time monitoring and management of the transaction processor

This architecture provides a clean separation of concerns, allowing the transaction processor to focus on high-performance message handling while the web portal delivers a user-friendly monitoring experience.

## Features

### Transaction Processor
- TCP/IP server for accepting financial transactions
- AS2805 message parsing and handling
- Transaction validation and processing
- Comprehensive logging and error handling
- Extensible architecture for custom processing rules

### Web Portal
- Real-time dashboard with transaction metrics
- Detailed transaction viewer with search and filtering
- System status monitoring
- Historical transaction data with analytics
- Responsive design for desktop and mobile access

### Security Features
- **Field-level Encryption**: Sensitive transaction data (amount, terminal ID, merchant ID, raw message) is encrypted in the database
- **Comprehensive Audit Logging**: All system activities are logged with timestamps, user IDs, and IP addresses
- **Data Integrity Protection**: Transaction records include hash values to detect tampering
- **Access Tracking**: Every data access is logged with timestamps and counts
- **Security Headers**: HTTP security headers (CSP, HSTS, etc.) added to all responses
- **CSRF Protection**: Cross-Site Request Forgery protection for all forms
- **Secure Cookie Management**: Session cookies configured with secure flags
- **Transaction Integrity Verification**: Methods to verify transaction data hasn't been altered

## System Requirements

### Transaction Processor
- Java 11 or higher
- Maven for dependency management
- Network access for TCP/IP communication

### Web Portal
- Python 3.7 or higher
- Flask and SQLAlchemy
- PostgreSQL or SQLite database

## Quick Start

### Running the Web Portal

1. Install the required Python dependencies:
   ```
   pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator requests
   ```

2. Start the Flask application:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

3. Access the web portal at http://localhost:5000

### Running the Transaction Processor

1. Navigate to the transaction-processor directory:
   ```
   cd transaction-processor
   ```

2. Build the project with Maven:
   ```
   mvn clean package
   ```

3. Run the transaction processor:
   ```
   java -jar target/transaction-processor-1.0.0.jar
   ```

## Project Structure

```
├── transaction-processor      # Java backend component
│   ├── deploy                 # JPOS deployment descriptors
│   ├── src/main               # Source code
│       ├── java               # Java source files
│       └── resources          # Configuration files
├── web-portal                 # Python Flask frontend
│   ├── static                 # CSS, JavaScript, and other static assets
│   ├── templates              # HTML templates
│   ├── app.py                 # Flask application
│   ├── models.py              # Database models
│   └── routes.py              # Web routes and API endpoints
└── main.py                    # Entry point for the web portal
```

## Development

### Transaction Processor
The transaction processor is based on JPOS, which uses XML deployment descriptors for configuration. The main components are:

- **TransactionServer**: Handles incoming TCP/IP connections
- **AS2805MessageFactory**: Creates AS2805 message objects from raw data
- **TransactionProcessor**: Processes transactions based on business rules

### Web Portal
The web portal uses Flask and follows a standard MVC architecture:

- **Models**: Database models for transactions and system status
- **Routes**: API endpoints and page rendering
- **Templates**: HTML templates with Bootstrap styling
- **Static Assets**: CSS and JavaScript for interactive features

## Documentation

For more detailed documentation, see:

- [AS2805 Standard](https://www.standards.org.au/standards-catalogue/sa-snz/communication/it-005/as--2805-dot-1-dot-1-2011)
- [JPOS Documentation](http://jpos.org/doc/javadoc/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- JPOS Project for the excellent financial transaction framework
- Flask and SQLAlchemy for web application components
- Bootstrap for responsive UI components