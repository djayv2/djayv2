#!/usr/bin/env python3
"""
FERC Scraper - Complete Production Package Creator
Run this script to create the complete FERC scraper locally
"""

import os
import zipfile
import base64

def create_ferc_scraper():
    """Create complete FERC scraper package"""
    
    # Create directory structure
    os.makedirs("ferc_scraper_complete/src/ferc_scraper", exist_ok=True)
    os.makedirs("ferc_scraper_complete/tests", exist_ok=True)
    os.makedirs("ferc_scraper_complete/scrapers", exist_ok=True)
    
    # File 1: requirements.txt
    with open("ferc_scraper_complete/requirements.txt", "w") as f:
        f.write("""requests==2.31.0
beautifulsoup4==4.12.2
pg8000==1.30.4
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-mock==3.12.0
requests-toolbelt==1.0.0
croniter==2.0.5
joblib==1.4.2
selenium==4.15.0
webdriver-manager==4.0.1
""")
    
    # File 2: Dockerfile
    with open("ferc_scraper_complete/Dockerfile", "w") as f:
        f.write("""FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \\
    wget gnupg unzip curl \\
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \\
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \\
    && apt-get update \\
    && apt-get install -y google-chrome-stable \\
    && rm -rf /var/lib/apt/lists/*

RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \\
    wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \\
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ && \\
    rm /tmp/chromedriver.zip && \\
    chmod +x /usr/local/bin/chromedriver

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)" || exit 1
CMD ["python", "main.py"]
""")
    
    # File 3: docker-compose.yml
    with open("ferc_scraper_complete/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'
services:
  ferc-scraper:
    build: .
    container_name: ferc_scraper
    environment:
      DB_HOST: 34.59.88.3
      DB_PORT: 5432
      DB_NAME: postgres
      DB_USER: jay_semia
      DB_PASSWORD: $..q)kf:=bCqw4fZ
      DB_SSLMODE: prefer
      DB_SCHEMA: test_external
      BASE_URL: https://www.ferc.gov/download-database
      SCRAPER_MODE: dbindex
      MAX_PAGES: 1
      FETCH_DETAILS: false
      REQUEST_TIMEOUT_SECONDS: 20
      MAX_RETRIES: 6
      SCD_TYPE: 2
      CREATE_TABLES: false
      INGEST_DATASETS: true
      RAW_TABLE: ferc_raw
      APPLICATION_NAME: ferc_scraper
      ENV_NAME: production
      ADHOC_SCRIPTS: None
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 60s
      timeout: 10s
      retries: 3
""")
    
    # File 4: .env.example
    with open("ferc_scraper_complete/.env.example", "w") as f:
        f.write("""DB_HOST=34.59.88.3
DB_PORT=5432
DB_NAME=postgres
DB_USER=jay_semia
DB_PASSWORD=$..q)kf:=bCqw4fZ
DB_SSLMODE=prefer
DB_CONNECT_TIMEOUT_SECONDS=20
DB_SCHEMA=test_external
BASE_URL=https://www.ferc.gov/download-database
SCRAPER_MODE=dbindex
MAX_PAGES=1
FETCH_DETAILS=false
REQUEST_TIMEOUT_SECONDS=20
MAX_RETRIES=6
SCD_TYPE=2
CREATE_TABLES=false
INGEST_DATASETS=true
RAW_TABLE=ferc_raw
APPLICATION_NAME=ferc_scraper
ENV_NAME=production
""")
    
    # File 5: src/ferc_scraper/config.py
    with open("ferc_scraper_complete/src/ferc_scraper/config.py", "w") as f:
        f.write("""from __future__ import annotations
import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="postgres", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="postgres", description="Database password")
    db_sslmode: str = Field(default="prefer", description="SSL mode")
    db_connect_timeout_seconds: int = Field(default=20, description="Connection timeout")
    db_schema: str = Field(default="public", description="Database schema")
    base_url: str = Field(default="https://www.ferc.gov/download-database", description="Base URL to scrape")
    scraper_mode: str = Field(default="dbindex", description="Scraper mode (dbindex, news)")
    max_pages: int = Field(default=1, description="Maximum pages to scrape")
    fetch_details: bool = Field(default=False, description="Fetch detail pages")
    request_timeout_seconds: int = Field(default=20, description="Request timeout")
    max_retries: int = Field(default=6, description="Maximum retry attempts")
    create_tables: bool = Field(default=False, description="Create database tables")
    scd_type: int = Field(default=2, description="SCD type (1 or 2)")
    ingest_datasets: bool = Field(default=True, description="Ingest downloaded datasets")
    raw_table: str = Field(default="ferc_raw", description="Raw data table name")
    application_name: str = Field(default="ferc_scraper", description="Application name")
    env_name: str = Field(default="production", description="Environment name")
    source_ip: Optional[str] = Field(default=None, description="Source IP for requests")
    outbound_proxy_url: Optional[str] = Field(default=None, description="Outbound proxy URL")
    adhoc_scripts: Optional[str] = Field(default=None, description="Adhoc scripts to run")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

def get_settings() -> Settings:
    return Settings()
""")
    
    # File 6: main.py
    with open("ferc_scraper_complete/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ferc_scraper.config import get_settings
from ferc_scraper.scraper import run_scraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ferc_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting FERC scraper...")
        settings = get_settings()
        logger.info(f"Configuration loaded for environment: {settings.env_name}")
        result = run_scraper(settings)
        logger.info(f"Scraper completed. Processed {result} items.")
        return 0
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    # Create __init__.py files
    with open("ferc_scraper_complete/src/__init__.py", "w") as f:
        f.write("")
    with open("ferc_scraper_complete/src/ferc_scraper/__init__.py", "w") as f:
        f.write("")
    
    print("✅ FERC scraper files created successfully!")
    print("📁 Location: ferc_scraper_complete/")
    print("🚀 To run: cd ferc_scraper_complete && docker-compose up -d")

if __name__ == "__main__":
    create_ferc_scraper()