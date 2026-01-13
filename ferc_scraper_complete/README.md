# FERC Database Scraper

A production-ready Python scraper for the Federal Energy Regulatory Commission (FERC) database downloads, featuring Cloudflare bypass, PostgreSQL integration, and SCD1/SCD2 data warehousing.

## 🚀 Features

- **Cloudflare Bypass**: Selenium-based scraping to handle Cloudflare protection
- **PostgreSQL Integration**: Full database integration with pg8000 driver
- **SCD1/SCD2 Support**: Slowly Changing Dimension implementation for data warehousing
- **Docker Deployment**: Complete containerization with docker-compose
- **Data Ingestion**: Automatic CSV/ZIP file processing and ingestion
- **Scheduling**: Cron-based job scheduling with joblib
- **Monitoring**: Health checks and comprehensive logging

## 📋 Prerequisites

- Docker and Docker Compose
- PostgreSQL (included in docker-compose)
- Python 3.11+ (for local development)

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/djayv2/djayv2.git
cd djayv2
git checkout cursor/build-ferc-website-scraper-with-docker-and-postgresql-5f58
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Deploy with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ferc-scraper

# Check status
docker-compose ps
```

### 4. Access Services

- **pgAdmin**: http://localhost:8080 (admin@ferc.local / admin)
- **PostgreSQL**: localhost:5432
- **Scraper Logs**: `docker-compose logs ferc-scraper`

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ferc_data
DB_USER=ferc_user
DB_PASSWORD=your_secure_password
DB_SCHEMA=ferc_schema

# Scraper Configuration
BASE_URL=https://www.ferc.gov/download-database
SCRAPER_MODE=dbindex
MAX_PAGES=1
FETCH_DETAILS=false
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3
SCD_TYPE=2

# Data Processing
CREATE_TABLES=true
INGEST_DATASETS=true
RAW_TABLE=ferc_raw
```

### Scraper Modes

- **`dbindex`**: Scrape FERC database download page (default)
- **`news`**: Scrape FERC news articles (legacy mode)

### SCD Types

- **`1`**: Type 1 - Overwrite existing records
- **`2`**: Type 2 - Keep history with versioning (recommended)

## 📊 Database Schema

### Documents Table (SCD2)

```sql
CREATE TABLE ferc_schema.documents (
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
CREATE TABLE ferc_schema.ferc_raw (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    dataset_name VARCHAR(255),
    row_data JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR(64)
);
```

## 🧪 Testing

### Run Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/ -v
```

### Run Production Test

```bash
python test_production_scraper.py
```

### Test Selenium Scraper

```bash
python test_selenium_scraper.py
```

## 📈 Monitoring

### Health Checks

```bash
# Check scraper health
docker-compose exec ferc-scraper python -c "import sys; sys.exit(0)"

# Check database health
docker-compose exec postgres pg_isready -U ferc_user -d ferc_data
```

### Logs

```bash
# View scraper logs
docker-compose logs -f ferc-scraper

# View database logs
docker-compose logs -f postgres
```

## 🔄 Scheduling

The scraper uses cron-based scheduling defined in `run_jobs.json`:

```json
{
    "scraper_name": {
        "path_to_job": "./scrapers/scraper_name.py",
        "schedule": "* * * * *",
        "size": "small"
    }
}
```

## 🐳 Docker Commands

### Build and Run

```bash
# Build image
docker build -t ferc-scraper .

# Run container
docker run --env-file .env ferc-scraper

# Run with docker-compose
docker-compose up -d
```

### Management

```bash
# Stop services
docker-compose down

# Restart scraper
docker-compose restart ferc-scraper

# View resource usage
docker-compose stats
```

## 🚨 Troubleshooting

### Cloudflare Issues

If Cloudflare blocking persists:

1. **Increase timeouts**: Set `REQUEST_TIMEOUT_SECONDS=60`
2. **Use proxy**: Configure `OUTBOUND_PROXY_URL`
3. **Manual verification**: Check if site is accessible in browser

### Database Connection Issues

```bash
# Check database connectivity
docker-compose exec ferc-scraper python -c "
from ferc_scraper.config import get_settings
from ferc_scraper.storage import PostgresStorage
settings = get_settings()
with PostgresStorage(settings) as storage:
    print('Database connection successful')
"
```

### Selenium Issues

```bash
# Check Chrome installation
docker-compose exec ferc-scraper google-chrome --version

# Check ChromeDriver
docker-compose exec ferc-scraper chromedriver --version
```

## 📝 Development

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run scraper
python main.py
```

### Adding New Scrapers

1. Create new scraper in `scrapers/` directory
2. Add job configuration to `run_jobs.json`
3. Update tests in `tests/` directory

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details

---

**Note**: This scraper is designed to respect FERC's terms of service and implement appropriate rate limiting and error handling.
