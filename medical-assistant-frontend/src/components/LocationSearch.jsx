import React, { useState } from 'react';
import './LocationSearch.css';

const LocationSearch = ({ onSearch, loading }) => {
  const [pinCode, setPinCode] = useState('');

  const handleSearch = () => {
    if (pinCode.length === 6) {
      onSearch(pinCode);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && pinCode.length === 6) {
      handleSearch();
    }
  };

  return (
    <div className="location-search">
      <h3>🏥 Find Nearby Specialists</h3>
      <div className="search-input-group">
        <input
          type="text"
          placeholder="Enter PIN Code (e.g., 201301)"
          value={pinCode}
          onChange={(e) => setPinCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          onKeyPress={handleKeyPress}
          maxLength={6}
          className="pin-input"
        />
        <button 
          onClick={handleSearch}
          disabled={loading || pinCode.length !== 6}
          className="search-btn"
        >
          {loading ? '🔍 Searching...' : '🔍 Find Hospitals'}
        </button>
      </div>
      <p className="search-hint">Enter your 6-digit PIN code to find nearby healthcare facilities</p>
    </div>
  );
};

export default LocationSearch;
