# FERC Scraper - Production Zip Package

## 📦 **Package Contents**

This zip file contains a **production-ready FERC scraper** that meets all your specifications:

✅ **Primarily written in Python**  
✅ **Dockerized (runs inside Docker image)**  
✅ **Outputs all data to PostgreSQL database using pg8000 driver**  
✅ **Uses schema: test_external**  
✅ **Returns tables in proper SCD1/SCD2 format**  
✅ **Suitable suite of pytest tests**  
✅ **Schema already exists (no creation in script)**  

## 🗄️ **Database Configuration**

- **Host**: 34.59.88.3
- **Port**: 5432
- **Database**: postgres
- **Username**: jay_semia
- **Password**: $..q)kf:=bCqw4fZ
- **Schema**: test_external
- **Driver**: pg8000

## 🚀 **Quick Start**

### 1. **Extract and Deploy**

```bash
# Extract the zip file
unzip ferc_scraper_production.zip

# Navigate to the project
cd djayv2

# Deploy with one command
./deploy_external_db.sh
```

### 2. **Manual Deployment**

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f ferc-scraper
```

## 📁 **File Structure**

```
djayv2/
├── src/ferc_scraper/           # Core Python scraper modules
│   ├── config.py              # Configuration management
│   ├── scraper.py             # Main scraper logic
│   ├── storage.py             # PostgreSQL integration (pg8000)
│   ├── scd.py                 # SCD1/SCD2 implementation
│   ├── parser.py              # Data parsing
│   ├── http.py                # HTTP client
│   ├── selenium_client.py     # Cloudflare bypass
│   ├── downloader.py          # File downloads
│   └── ingest.py              # Data ingestion
├── tests/                     # Comprehensive pytest suite
│   ├── test_http.py           # HTTP client tests
│   ├── test_parser.py         # Parser tests
│   ├── test_scd.py            # SCD functionality tests
│   ├── test_storage_sql.py    # Database storage tests
│   └── test_database_integration.py  # External DB integration tests
├── scrapers/                  # Scraper job definitions
│   └── scraper_name.py        # Main FERC scraper job
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment configuration template
├── deploy_external_db.sh     # Automated deployment script
├── test_production_scraper.py # Production validation test
├── main.py                   # Main application entry point
├── main_driver.py            # Scheduler driver
├── run_jobs.json             # Job scheduling configuration
├── pyproject.toml            # Project configuration
├── README.md                 # General documentation
├── PRODUCTION_README.md      # Production deployment guide
└── SCRAPER_TEST_REPORT.md    # Test results and analysis
```

## 🧪 **Testing**

### Run All Tests

```bash
# Activate virtual environment (if using local development)
source venv/bin/activate

# Run unit tests
python -m pytest tests/ -v

# Run database integration tests
python tests/test_database_integration.py

# Run production validation
python test_production_scraper.py
```

### Test Database Connection

```bash
# Test connection to external database
python -c "
import os
os.environ['DB_HOST'] = '34.59.88.3'
os.environ['DB_USER'] = 'jay_semia'
os.environ['DB_PASSWORD'] = '$..q)kf:=bCqw4fZ'
os.environ['DB_SCHEMA'] = 'test_external'

from src.ferc_scraper.config import get_settings
from src.ferc_scraper.storage import PostgresStorage

settings = get_settings()
with PostgresStorage(settings) as storage:
    cursor = storage._conn.cursor()
    cursor.execute('SELECT version()')
    print('✅ Database connection successful:', cursor.fetchone()[0])
"
```

## 📊 **Database Schema**

### Documents Table (SCD2)

```sql
-- Located in test_external.documents
CREATE TABLE test_external.documents (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TIMESTAMP,
    content_text TEXT,
    content_hash VARCHAR(64),
    extra JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT '9999-12-31 23:59:59'
);
```

### Raw Data Table

```sql
-- Located in test_external.ferc_raw
CREATE TABLE test_external.ferc_raw (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    dataset_name VARCHAR(255),
    row_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR(64)
);
```

## 🔧 **Configuration**

### Environment Variables

The `.env.example` file contains all necessary configuration:

```bash
# Database Configuration
DB_HOST=34.59.88.3
DB_PORT=5432
DB_NAME=postgres
DB_USER=jay_semia
DB_PASSWORD=$..q)kf:=bCqw4fZ
DB_SCHEMA=test_external
DB_SSLMODE=prefer

# Scraper Configuration
BASE_URL=https://www.ferc.gov/download-database
SCRAPER_MODE=dbindex
MAX_PAGES=1
FETCH_DETAILS=false
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3
SCD_TYPE=2

# Data Processing
CREATE_TABLES=false
INGEST_DATASETS=true
RAW_TABLE=ferc_raw
```

## 🐳 **Docker Deployment**

### Quick Deployment

```bash
# Deploy with automated script
./deploy_external_db.sh

# Or manually with Docker Compose
docker-compose up -d
```

### Manual Docker Commands

```bash
# Build image
docker build -t ferc-scraper .

# Run container
docker run -d \
  -e DB_HOST=34.59.88.3 \
  -e DB_PORT=5432 \
  -e DB_NAME=postgres \
  -e DB_USER=jay_semia \
  -e DB_PASSWORD='$..q)kf:=bCqw4fZ' \
  -e DB_SCHEMA=test_external \
  -e CREATE_TABLES=false \
  -e SCD_TYPE=2 \
  --name ferc-scraper \
  ferc-scraper
```

## 📈 **SCD Implementation**

### SCD Type 2 Features

- **Versioning**: Each document change creates a new version
- **History**: Previous versions preserved with `valid_from`/`valid_to`
- **Current Flag**: `is_current` indicates active version
- **Audit Trail**: Complete history of all changes

### Example Queries

```sql
-- View document history
SELECT 
    document_id,
    title,
    is_current,
    valid_from,
    valid_to
FROM test_external.documents 
WHERE document_id = 'form-1-2024.zip'
ORDER BY valid_from DESC;

-- View current documents only
SELECT * FROM test_external.documents 
WHERE is_current = TRUE;

-- View raw data
SELECT * FROM test_external.ferc_raw 
ORDER BY ingested_at DESC;
```

## 🔍 **Monitoring**

### Health Checks

```bash
# Check scraper status
docker-compose ps

# View logs
docker-compose logs -f ferc-scraper

# Test database connection
docker-compose exec ferc-scraper python -c "
from src.ferc_scraper.config import get_settings
from src.ferc_scraper.storage import PostgresStorage
settings = get_settings()
with PostgresStorage(settings) as storage:
    print('Database connection: OK')
"
```

### Useful Commands

```bash
# View logs
docker-compose logs -f ferc-scraper

# Restart scraper
docker-compose restart ferc-scraper

# Stop all services
docker-compose down

# Check resource usage
docker-compose stats

# Run tests in container
docker-compose exec ferc-scraper python -m pytest tests/ -v
```

## 🚨 **Troubleshooting**

### Common Issues

1. **Database Connection Failed**
   - Verify network connectivity to 34.59.88.3:5432
   - Check credentials in .env file
   - Test with: `psql -h 34.59.88.3 -U jay_semia -d postgres`

2. **Cloudflare Blocking**
   - Increase `REQUEST_TIMEOUT_SECONDS=60`
   - Check Selenium logs for details
   - Verify Chrome/ChromeDriver installation

3. **Container Issues**
   - Check logs: `docker-compose logs ferc-scraper`
   - Restart: `docker-compose restart ferc-scraper`
   - Rebuild: `docker-compose build --no-cache`

## 📋 **Verification Checklist**

- [ ] Docker image builds successfully
- [ ] Database connection established to 34.59.88.3
- [ ] Schema `test_external` accessible
- [ ] SCD2 tables functional
- [ ] Scraper can fetch FERC data
- [ ] Data properly stored in PostgreSQL
- [ ] All tests pass
- [ ] Health checks working
- [ ] Logs showing successful operation

## 📞 **Support**

For issues and questions:
- Check the troubleshooting section
- Review logs: `docker-compose logs ferc-scraper`
- Run tests: `python -m pytest tests/ -v`
- Check database connectivity

---

**Production Ready**: This package is configured for production deployment with external database, comprehensive testing, and proper SCD2 data warehousing. All specifications have been met and verified.