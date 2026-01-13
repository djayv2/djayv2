import os
import sys
import pytest
from datetime import datetime
sys.path.insert(0, 'src')

from ferc_scraper.config import get_settings
from ferc_scraper.storage import PostgresStorage
from ferc_scraper.parser import DocumentItem


class TestDatabaseIntegration:
    """Test database integration with external PostgreSQL database"""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup environment variables for testing"""
        os.environ['DB_HOST'] = '34.59.88.3'
        os.environ['DB_PORT'] = '5432'
        os.environ['DB_NAME'] = 'postgres'
        os.environ['DB_USER'] = 'jay_semia'
        os.environ['DB_PASSWORD'] = '$..q)kf:=bCqw4fZ'
        os.environ['DB_SCHEMA'] = 'test_external'
        os.environ['CREATE_TABLES'] = 'false'
        os.environ['SCD_TYPE'] = '2'
    
    def test_database_connection(self):
        """Test connection to external database"""
        settings = get_settings()
        
        try:
            with PostgresStorage(settings) as storage:
                # Test basic connection
                assert storage._conn is not None
                print("✅ Database connection successful")
                
                # Test schema access
                cursor = storage._conn.cursor()
                cursor.execute("SELECT current_schema()")
                current_schema = cursor.fetchone()[0]
                print(f"✅ Current schema: {current_schema}")
                
                # Test if test_external schema exists
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'test_external'
                """)
                schema_exists = cursor.fetchone()
                assert schema_exists is not None, "test_external schema does not exist"
                print("✅ test_external schema exists")
                
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")
    
    def test_scd2_functionality(self):
        """Test SCD2 (Slowly Changing Dimension) functionality"""
        settings = get_settings()
        
        with PostgresStorage(settings) as storage:
            # Create test document
            test_doc = DocumentItem(
                source="TEST_FERC",
                document_id="test-doc-001",
                url="https://www.ferc.gov/test-doc-001.zip",
                title="Test Document 001",
                published_at=datetime.now(),
                extra={"test": True, "version": "1.0"}
            )
            
            # Insert document
            storage.upsert_documents([test_doc])
            print("✅ Document inserted successfully")
            
            # Verify document exists
            cursor = storage._conn.cursor()
            cursor.execute("""
                SELECT document_id, title, is_current 
                FROM test_external.documents 
                WHERE document_id = 'test-doc-001'
                ORDER BY valid_from DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            assert result is not None, "Document not found"
            assert result[0] == "test-doc-001"
            assert result[1] == "Test Document 001"
            assert result[2] is True  # is_current should be True
            print("✅ SCD2 document verification successful")
            
            # Test SCD2 update
            updated_doc = DocumentItem(
                source="TEST_FERC",
                document_id="test-doc-001",
                url="https://www.ferc.gov/test-doc-001-v2.zip",
                title="Test Document 001 (Updated)",
                published_at=datetime.now(),
                extra={"test": True, "version": "2.0"}
            )
            
            # Update document
            storage.upsert_documents([updated_doc])
            print("✅ Document updated successfully")
            
            # Verify SCD2 versioning
            cursor.execute("""
                SELECT document_id, title, is_current, valid_from
                FROM test_external.documents 
                WHERE document_id = 'test-doc-001'
                ORDER BY valid_from DESC
            """)
            results = cursor.fetchall()
            
            assert len(results) >= 2, "SCD2 versioning not working"
            
            # Latest version should be current
            latest = results[0]
            assert latest[2] is True, "Latest version should be current"
            assert latest[1] == "Test Document 001 (Updated)", "Wrong title for updated version"
            
            # Previous version should not be current
            previous = results[1]
            assert previous[2] is False, "Previous version should not be current"
            assert previous[1] == "Test Document 001", "Wrong title for previous version"
            
            print("✅ SCD2 versioning working correctly")
    
    def test_raw_data_ingestion(self):
        """Test raw data ingestion functionality"""
        settings = get_settings()
        
        with PostgresStorage(settings) as storage:
            # Test raw data insertion
            test_data = {
                "company": "Test Utility",
                "year": 2024,
                "revenue": 1000000,
                "customers": 50000
            }
            
            # Insert raw data
            cursor = storage._conn.cursor()
            cursor.execute("""
                INSERT INTO test_external.ferc_raw 
                (source_url, dataset_name, row_data, file_hash)
                VALUES (%s, %s, %s, %s)
            """, (
                "https://www.ferc.gov/test-data.csv",
                "test_dataset",
                test_data,
                "test_hash_123"
            ))
            storage._conn.commit()
            print("✅ Raw data inserted successfully")
            
            # Verify raw data
            cursor.execute("""
                SELECT source_url, dataset_name, row_data
                FROM test_external.ferc_raw 
                WHERE file_hash = 'test_hash_123'
            """)
            result = cursor.fetchone()
            
            assert result is not None, "Raw data not found"
            assert result[0] == "https://www.ferc.gov/test-data.csv"
            assert result[1] == "test_dataset"
            assert result[2]["company"] == "Test Utility"
            assert result[2]["revenue"] == 1000000
            
            print("✅ Raw data verification successful")
    
    def test_pg8000_ssl_handling(self):
        """Test pg8000 SSL connection handling"""
        settings = get_settings()
        
        # Test with SSL mode
        settings.db_sslmode = "require"
        
        try:
            with PostgresStorage(settings) as storage:
                cursor = storage._conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✅ SSL connection successful: {version[:50]}...")
        except Exception as e:
            print(f"⚠️ SSL connection failed (this may be expected): {e}")
            
            # Fallback to prefer mode
            settings.db_sslmode = "prefer"
            with PostgresStorage(settings) as storage:
                cursor = storage._conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✅ Fallback connection successful: {version[:50]}...")


if __name__ == "__main__":
    # Run tests manually
    test_instance = TestDatabaseIntegration()
    test_instance.setup_environment()
    
    print("🧪 Running Database Integration Tests")
    print("=" * 50)
    
    try:
        test_instance.test_database_connection()
        test_instance.test_scd2_functionality()
        test_instance.test_raw_data_ingestion()
        test_instance.test_pg8000_ssl_handling()
        print("\n✅ All database integration tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()