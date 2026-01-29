import React from 'react';
import './HospitalList.css';

const HospitalList = ({ locationInfo }) => {
  if (!locationInfo || !locationInfo.hospitals || locationInfo.hospitals.length === 0) {
    return null;
  }

  // Helper function to get today's opening hours
  const getTodayHours = (openingHours) => {
    if (!openingHours || openingHours.length === 0) return null;
    
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = days[new Date().getDay()];
    
    const todayHours = openingHours.find(hours => hours.startsWith(today));
    return todayHours ? todayHours.split(': ')[1] : null;
  };

  return (
    <div className="hospitals-container">
      <h3>
        📍 Found {locationInfo.hospitals.length} Healthcare Facilities
        {locationInfo.specialty_detected && (
          <span className="specialty-badge"> ({locationInfo.specialty_detected})</span>
        )}
      </h3>

      <div className="hospitals-list">
        {locationInfo.hospitals.map((hospital, idx) => (
          <div key={idx} className="hospital-card">
            <div className="hospital-header">
              <div className="hospital-title-section">
                <h4>{hospital.name}</h4>
                <span className="hospital-type">{hospital.type}</span>
              </div>
              
              {/* Rating Section */}
              {hospital.rating > 0 && (
                <div className="hospital-rating">
                  <span className="rating-stars">⭐ {hospital.rating.toFixed(1)}</span>
                  <span className="rating-count">({hospital.total_ratings} reviews)</span>
                </div>
              )}
            </div>
            
            <div className="hospital-details">
              {/* Address */}
              <p className="hospital-address">
                <span className="icon">📍</span>
                <span>{hospital.address}</span>
              </p>
              
              {/* Distance */}
              <p className="hospital-distance">
                <span className="icon">📏</span>
                <strong>{hospital.distance_km} km</strong> away
              </p>

              {/* Business Hours */}
              <div className="hospital-hours">
                {hospital.is_open_now !== null && (
                  <div className={`status-badge ${hospital.is_open_now ? 'open' : 'closed'}`}>
                    {hospital.is_open_now ? '🟢 Open Now' : '🔴 Closed'}
                  </div>
                )}
                
                {getTodayHours(hospital.opening_hours) && (
                  <p className="today-hours">
                    <span className="icon">🕐</span>
                    <span>Today: {getTodayHours(hospital.opening_hours)}</span>
                  </p>
                )}
              </div>

              {/* All Week Hours (Collapsible) */}
              {hospital.opening_hours && hospital.opening_hours.length > 0 && (
                <details className="full-hours">
                  <summary>View All Hours</summary>
                  <ul className="hours-list">
                    {hospital.opening_hours.map((hours, i) => (
                      <li key={i}>{hours}</li>
                    ))}
                  </ul>
                </details>
              )}

              {/* Business Status Warning */}
              {hospital.business_status !== 'OPERATIONAL' && (
                <div className="status-warning">
                  ⚠️ Status: {hospital.business_status.replace('_', ' ')}
                </div>
              )}

              {/* Google Maps Link */}
              <a 
                href={hospital.google_maps_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="maps-link"
              >
                🗺️ View on Google Maps
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HospitalList;
