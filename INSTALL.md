# Installation Guide for SillyPostilion

This guide provides detailed instructions for setting up the SillyPostilion transaction processing system on your development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

### For the Web Portal (Python)
- Python 3.7 or higher
- pip (Python package manager)
- Git

### For the Transaction Processor (Java)
- Java 11 or higher
- Maven 3.6 or higher

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sillypostilion.git
cd sillypostilion
```

### 2. Set Up the Web Portal

#### Install Python Dependencies

```bash
pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator requests
```

#### Initialize the Database

For SQLite (development):
```bash
# The database will be automatically created at first run
```

For PostgreSQL (production):
```bash
# Create a PostgreSQL database
createdb sillypostilion

# Set the DATABASE_URL environment variable
export DATABASE_URL=postgresql://username:password@localhost/sillypostilion
```

### A. Run the Web Portal

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

The web portal will be accessible at http://localhost:5000

### 3. Set Up the Transaction Processor

#### Build the Java Project

```bash
cd transaction-processor
mvn clean package
```

#### Configure the Transaction Processor

Edit the deployment descriptors in the `deploy` directory if needed:

- **00_logger.xml**: Logging configuration
- **01_channel.xml**: Communication channel settings
- **10_transaction_manager.xml**: Transaction processing rules

### B. Run the Transaction Processor

```bash
java -jar target/transaction-processor-1.0.0.jar
```

The transaction processor will start and listen for connections on the configured port (default: 8000).

## Configuration Options

### Web Portal

The web portal can be configured using environment variables:

- **DATABASE_URL**: Database connection string (default: SQLite)
- **TRANSACTION_PROCESSOR_API**: URL of the transaction processor API (default: http://localhost:8000/api)
- **SESSION_SECRET**: Secret key for session management

### Transaction Processor

The transaction processor is configured using XML descriptors in the `deploy` directory:

- Port and host settings in `01_channel.xml`
- Processing rules in `10_transaction_manager.xml`

## Troubleshooting

### Web Portal Issues

1. **Database Connection Errors**:
   - Verify the DATABASE_URL environment variable
   - Ensure the database server is running
   - Check database user permissions

2. **Template Errors**:
   - Clear browser cache
   - Verify all template files exist in the `templates` directory

### Transaction Processor Issues

1. **Compilation Errors**:
   - Ensure Java 11+ is installed and set as JAVA_HOME
   - Update Maven dependencies: `mvn dependency:resolve`

2. **Runtime Errors**:
   - Check the logs for detailed error messages
   - Verify the configuration in XML deployment descriptors

## Running Tests

### Web Portal Tests

```bash
pytest web-portal/tests/
```

### Transaction Processor Tests

```bash
cd transaction-processor
mvn test
```

## Deployment

For production deployment, consider:

1. Using a production WSGI server for the web portal
2. Setting up proper logging and monitoring
3. Configuring a reverse proxy (Nginx/Apache)
4. Implementing proper security measures (HTTPS, firewall rules)

See the README.md for more information on production deployment.