"""
Add 25 Hospital Records to Database
Run this script to populate the database with hospital data.

Usage:
    python add_hospitals.py
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.hospitals import ensure_hospitals_table, get_db_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def add_hospitals():
    """Add 25 hospital records to the database."""
    
    hospitals = [
        # Delhi Hospitals
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
        },
        # Mumbai Hospitals
        {
            "name": "Lilavati Hospital",
            "address": "A-791, Bandra Reclamation, Bandra West, Mumbai, Maharashtra 400050",
            "lat": 19.0596,
            "lon": 72.8295,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-22-26751000",
            "emergency_services": True
        },
        {
            "name": "Jaslok Hospital",
            "address": "15, Dr. G. Deshmukh Marg, Pedder Road, Mumbai, Maharashtra 400026",
            "lat": 18.9667,
            "lon": 72.8083,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-22-66573000",
            "emergency_services": True
        },
        {
            "name": "Kokilaben Dhirubhai Ambani Hospital",
            "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West, Mumbai, Maharashtra 400053",
            "lat": 19.1333,
            "lon": 72.8333,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-22-30999999",
            "emergency_services": True
        },
        {
            "name": "Bombay Hospital",
            "address": "12, New Marine Lines, Mumbai, Maharashtra 400020",
            "lat": 18.9444,
            "lon": 72.8333,
            "type": "general",
            "specialty": None,
            "phone": "+91-22-22067676",
            "emergency_services": True
        },
        {
            "name": "Tata Memorial Hospital",
            "address": "Dr. E Borges Marg, Parel, Mumbai, Maharashtra 400012",
            "lat": 18.9981,
            "lon": 72.8425,
            "type": "specialty",
            "specialty": "oncology",
            "phone": "+91-22-24177000",
            "emergency_services": True
        },
        # Bangalore Hospitals
        {
            "name": "Narayana Health City",
            "address": "258/A, Bommasandra Industrial Area, Anekal Taluk, Bangalore, Karnataka 560099",
            "lat": 12.8444,
            "lon": 77.6603,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-80-27835000",
            "emergency_services": True
        },
        {
            "name": "Manipal Hospital",
            "address": "98, HAL Old Airport Rd, Kodihalli, Bangalore, Karnataka 560017",
            "lat": 12.9716,
            "lon": 77.5946,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-80-25023456",
            "emergency_services": True
        },
        {
            "name": "Apollo Hospital Bangalore",
            "address": "154/11, Bannerghatta Road, Bangalore, Karnataka 560076",
            "lat": 12.8996,
            "lon": 77.6014,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-80-26304050",
            "emergency_services": True
        },
        {
            "name": "Fortis Hospital",
            "address": "154/9, Bannerghatta Road, Opposite IIM-B, Bangalore, Karnataka 560076",
            "lat": 12.8996,
            "lon": 77.6014,
            "type": "general",
            "specialty": None,
            "phone": "+91-80-66214444",
            "emergency_services": True
        },
        {
            "name": "Columbia Asia Hospital",
            "address": "26/4, Brigade Gateway, Malleshwaram West, Bangalore, Karnataka 560055",
            "lat": 12.9716,
            "lon": 77.5946,
            "type": "general",
            "specialty": None,
            "phone": "+91-80-41791000",
            "emergency_services": True
        },
        # Chennai Hospitals
        {
            "name": "Apollo Hospitals",
            "address": "21, Greams Lane, Off Greams Road, Chennai, Tamil Nadu 600006",
            "lat": 13.0827,
            "lon": 80.2707,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-44-28290233",
            "emergency_services": True
        },
        {
            "name": "Fortis Malar Hospital",
            "address": "52, 1st Main Rd, Gandhi Nagar, Adyar, Chennai, Tamil Nadu 600020",
            "lat": 12.9716,
            "lon": 80.2206,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-44-42892222",
            "emergency_services": True
        },
        {
            "name": "MIOT International",
            "address": "4/112, Mount Poonamallee Road, Manapakkam, Chennai, Tamil Nadu 600089",
            "lat": 12.9716,
            "lon": 80.2206,
            "type": "general",
            "specialty": None,
            "phone": "+91-44-22492288",
            "emergency_services": True
        },
        # Hyderabad Hospitals
        {
            "name": "Apollo Hospitals",
            "address": "Jubilee Hills, Hyderabad, Telangana 500033",
            "lat": 17.4332,
            "lon": 78.4011,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-40-23607777",
            "emergency_services": True
        },
        {
            "name": "Continental Hospitals",
            "address": "Plot No. 3, Road No. 2, IT Park, Nanakramguda, Hyderabad, Telangana 500032",
            "lat": 17.4332,
            "lon": 78.4011,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-40-67121212",
            "emergency_services": True
        },
        {
            "name": "Yashoda Hospitals",
            "address": "Raj Bhavan Road, Somajiguda, Hyderabad, Telangana 500082",
            "lat": 17.4332,
            "lon": 78.4011,
            "type": "general",
            "specialty": None,
            "phone": "+91-40-24555555",
            "emergency_services": True
        },
        # Kolkata Hospitals
        {
            "name": "Apollo Gleneagles Hospitals",
            "address": "58, Canal Circular Road, Kadapara, Phool Bagan, Kolkata, West Bengal 700054",
            "lat": 22.5726,
            "lon": 88.3639,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-33-23203030",
            "emergency_services": True
        },
        {
            "name": "AMRI Hospitals",
            "address": "16/17, Gariahat Road, Dhakuria, Kolkata, West Bengal 700031",
            "lat": 22.5726,
            "lon": 88.3639,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-33-66060606",
            "emergency_services": True
        },
        {
            "name": "Fortis Hospital",
            "address": "730, Anandapur, E.M. Bypass Road, Kolkata, West Bengal 700107",
            "lat": 22.5726,
            "lon": 88.3639,
            "type": "general",
            "specialty": None,
            "phone": "+91-33-66284444",
            "emergency_services": True
        },
        # Pune Hospitals
        {
            "name": "Ruby Hall Clinic",
            "address": "40, Sassoon Road, Pune, Maharashtra 411001",
            "lat": 18.5204,
            "lon": 73.8567,
            "type": "emergency",
            "specialty": None,
            "phone": "+91-20-66455555",
            "emergency_services": True
        },
        {
            "name": "Jehangir Hospital",
            "address": "32, Sassoon Road, Pune, Maharashtra 411001",
            "lat": 18.5204,
            "lon": 73.8567,
            "type": "general",
            "specialty": None,
            "phone": "+91-20-66819999",
            "emergency_services": True
        }
    ]
    
    try:
        engine = get_db_engine()
        inserted_count = 0
        skipped_count = 0
        
        with engine.connect() as conn:
            for hospital in hospitals:
                try:
                    # Check if hospital already exists
                    check_query = text("SELECT id FROM hospitals WHERE name = :name AND address = :address")
                    result = conn.execute(check_query, {
                        "name": hospital["name"],
                        "address": hospital["address"]
                    })
                    
                    if result.fetchone():
                        logger.info(f"⏭️  Skipping (already exists): {hospital['name']}")
                        skipped_count += 1
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
                    
                    logger.info(f"✅ Inserted: {hospital['name']} - {hospital['address']}")
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error inserting {hospital['name']}: {e}")
                    continue
            
            conn.commit()
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"✅ Successfully inserted {inserted_count} hospitals")
            logger.info(f"⏭️  Skipped {skipped_count} hospitals (already exist)")
            logger.info(f"📊 Total hospitals in database: {inserted_count + skipped_count}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"❌ Error adding hospitals: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("Adding 25 Hospital Records to Database")
        logger.info("=" * 60)
        logger.info("")
        
        # Ensure table exists
        ensure_hospitals_table()
        logger.info("✅ Hospitals table verified")
        logger.info("")
        
        # Add hospitals
        add_hospitals()
        
        logger.info("")
        logger.info("✅ Process completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
        sys.exit(1)
