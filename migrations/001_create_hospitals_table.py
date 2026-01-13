"""
Database Migration: Create Hospitals Table with PostGIS
Run this script to set up the hospitals table with PostGIS support.

Usage:
    python migrations/001_create_hospitals_table.py
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.hospitals import ensure_hospitals_table, get_db_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def insert_sample_hospitals():
    """
    Insert sample hospital data for testing.
    Replace with your actual hospital data source.
    """
    try:
        engine = get_db_engine()
        
        # Sample hospitals (Delhi, India area)
        sample_hospitals = [
            {
                "name": "AIIMS Delhi",
                "address": "Ansari Nagar, New Delhi, Delhi 110029",
                "lat": 28.5673,
                "lon": 77.2088,
                "type": "emergency",
                "specialty": None,
                "phone": "+91-11-26588500",
                "emergency_services": True
            },
            {
                "name": "Apollo Hospital",
                "address": "Sarita Vihar, New Delhi, Delhi 110076",
                "lat": 28.5245,
                "lon": 77.2905,
                "type": "emergency",
                "specialty": None,
                "phone": "+91-11-26925858",
                "emergency_services": True
            },
            {
                "name": "Max Super Speciality Hospital",
                "address": "Saket, New Delhi, Delhi 110017",
                "lat": 28.5275,
                "lon": 77.2190,
                "type": "emergency",
                "specialty": None,
                "phone": "+91-11-26515050",
                "emergency_services": True
            },
            {
                "name": "Fortis Escorts Heart Institute",
                "address": "Okhla Road, New Delhi, Delhi 110025",
                "lat": 28.5450,
                "lon": 77.2800,
                "type": "specialty",
                "specialty": "cardiology",
                "phone": "+91-11-47135000",
                "emergency_services": True
            },
            {
                "name": "Indraprastha Apollo Hospitals",
                "address": "Sarita Vihar, New Delhi, Delhi 110076",
                "lat": 28.5245,
                "lon": 77.2905,
                "type": "general",
                "specialty": None,
                "phone": "+91-11-26925858",
                "emergency_services": False
            }
        ]
        
        with engine.connect() as conn:
            for hospital in sample_hospitals:
                # Check if hospital already exists
                check_query = text("SELECT id FROM hospitals WHERE name = :name")
                result = conn.execute(check_query, {"name": hospital["name"]})
                if result.fetchone():
                    logger.info(f"Hospital already exists: {hospital['name']}")
                    continue
                
                # Insert hospital
                insert_query = text("""
                    INSERT INTO hospitals (name, address, location, type, specialty, phone, emergency_services)
                    VALUES (
                        :name,
                        :address,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        :type,
                        :specialty,
                        :phone,
                        :emergency_services
                    )
                """)
                
                conn.execute(insert_query, {
                    "name": hospital["name"],
                    "address": hospital["address"],
                    "lat": hospital["lat"],
                    "lon": hospital["lon"],
                    "type": hospital["type"],
                    "specialty": hospital["specialty"],
                    "phone": hospital["phone"],
                    "emergency_services": hospital["emergency_services"]
                })
                logger.info(f"Inserted hospital: {hospital['name']}")
            
            conn.commit()
            logger.info(f"Successfully inserted {len(sample_hospitals)} sample hospitals")
            
    except Exception as e:
        logger.error(f"Error inserting sample hospitals: {e}")
        raise


if __name__ == "__main__":
    logger.info("Creating hospitals table with PostGIS support...")
    try:
        ensure_hospitals_table()
        logger.info("✅ Hospitals table created successfully")
        
        # Ask user if they want to insert sample data
        response = input("\nInsert sample hospital data? (y/n): ").strip().lower()
        if response == 'y':
            logger.info("Inserting sample hospitals...")
            insert_sample_hospitals()
            logger.info("✅ Sample hospitals inserted successfully")
        else:
            logger.info("Skipping sample data insertion")
        
        logger.info("\n✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
