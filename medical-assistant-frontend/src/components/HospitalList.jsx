import React from 'react';
import './HospitalList.css';

const HospitalList = ({ locationInfo }) => {
  if (!locationInfo || !locationInfo.hospitals || locationInfo.hospitals.length === 0) {
    return null;
  }

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
              <h4>{hospital.name}</h4>
              <span className="hospital-type">{hospital.type}</span>
            </div>
            
            <div className="hospital-details">
              <p className="hospital-address">
                <span className="icon">📍</span>
                {hospital.address}
              </p>
              
              <p className="hospital-phone">
                <span className="icon">📞</span>
                {hospital.phone}
              </p>
              
              {hospital.website && hospital.website !== 'N/A' && (
                <p className="hospital-website">
                  <span className="icon">🌐</span>
                  <a href={hospital.website} target="_blank" rel="noopener noreferrer">
                    Visit Website
                  </a>
                </p>
              )}
              
              <p className="hospital-distance">
                <span className="icon">📏</span>
                <strong>{hospital.distance_km} km</strong> away
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HospitalList;
