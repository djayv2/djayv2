# FERC Scraper - GitHub Gist Download Instructions

Since you're on Cursor web version without file access, here's how to get the complete FERC scraper:

## 🎯 **Option 1: GitHub Gist (Recommended)**

1. **Go to GitHub Gist**: https://gist.github.com/
2. **Create a new gist** with these files:

### File 1: `requirements.txt`
```
requests==2.31.0
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
```

### File 2: `Dockerfile`
```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1
CMD ["python", "main.py"]
```

### File 3: `docker-compose.yml`
```yaml
version: '3.8'
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
```

### File 4: `.env.example`
```
DB_HOST=34.59.88.3
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
```

3. **Download the gist** as a zip file
4. **Extract and use** the files

## 🎯 **Option 2: Ask Cursor Support**

Contact Cursor support and ask them to:
- Enable file download access for web version
- Provide access to workspace files
- Add export functionality for generated files

## 🎯 **Option 3: Use Different Platform**

Try using:
- **GitHub Codespaces** (has file access)
- **GitPod** (has file access)
- **Local Cursor** (has full file access)

The complete FERC scraper is ready - you just need a way to download it from your current environment.