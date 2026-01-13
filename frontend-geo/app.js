// API Configuration
const API_BASE = 'http://localhost:5005/medical-api/medicin';
const API_SYMPTOM_CHAT = `${API_BASE}/start_symptom_chat`;
const API_SYMPTOM_MESSAGE = `${API_BASE}/chat_symptoms`;
const API_OCR_ANALYZE = `${API_BASE}/ocr-geo/upload-and-analyze`;
const API_GEOLOCATION = `${API_BASE}/agent/geolocation`;

// State
let currentLanguage = localStorage.getItem('language') || 'en';
let translations = {};
let chatSessionId = null;
let map = null;
let markers = [];

// DOM Elements
const languageSelect = document.getElementById('language-select');
const symptomInput = document.getElementById('symptom-input');
const sendSymptomBtn = document.getElementById('send-symptom-btn');
const symptomChatMessages = document.getElementById('symptom-chat-messages');
const symptomResults = document.getElementById('symptom-results');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const documentResults = document.getElementById('document-results');

// Load translations
async function loadTranslations() {
    try {
        const response = await fetch('languages.json');
        translations = await response.json();
        updateUI();
    } catch (err) {
        console.error('Failed to load translations:', err);
        translations = { en: {} };
    }
}

// Update entire UI with current language
function updateUI() {
    const lang = translations[currentLanguage] || translations.en || {};
    
    // Update all text elements
    document.getElementById('app-title').textContent = lang.app_title || 'Medical Assistant';
    document.getElementById('language-label-text').textContent = lang.language || 'Language';
    document.getElementById('tab-symptoms-text').textContent = lang.tab_symptoms || 'Symptom Chat';
    document.getElementById('tab-document-text').textContent = lang.tab_document || 'Upload Report';
    document.getElementById('symptoms-title-text').textContent = lang.symptoms_title || 'Describe Your Symptoms';
    document.querySelector('#symptoms-tab .subtitle').textContent = lang.symptoms_subtitle || 'Enter your symptoms in any language. Our AI will analyze and recommend appropriate care.';
    document.getElementById('symptom-input').placeholder = lang.symptom_placeholder || 'Enter your symptoms...';
    document.getElementById('send-btn-text').textContent = lang.send || 'Send';
    document.getElementById('document-title-text').textContent = lang.document_title || 'Upload Medical Report';
    document.querySelector('#document-tab .subtitle').textContent = lang.document_subtitle || 'Upload your prescription, lab report, or medical document for analysis.';
    document.getElementById('upload-text').textContent = lang.upload_text || 'Drop your medical document here or click to browse';
    document.getElementById('upload-hint').textContent = lang.upload_hint || 'Supports: PDF, PNG, JPG, DOCX (Max 16MB)';
    document.getElementById('choose-file-text').textContent = lang.choose_file || 'Choose File';
    
    // Update language selector
    if (languageSelect) languageSelect.value = currentLanguage;
}

// Change language
function changeLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    updateUI();
}

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Clear results when switching tabs
    if (tabName === 'symptoms') {
        symptomResults.classList.add('hidden');
        symptomChatMessages.innerHTML = '';
    } else {
        documentResults.classList.add('hidden');
    }
}

// Make functions globally available
window.changeLanguage = changeLanguage;
window.showTab = showTab;

// Symptom Chat Functions
async function startSymptomChat() {
    try {
        const response = await fetch(API_SYMPTOM_CHAT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const data = await response.json();
            chatSessionId = data.session_id;
            addSymptomMessage('assistant', data.response || 'Hello! Please describe your symptoms.');
        }
    } catch (err) {
        console.error('Error starting chat:', err);
    }
}

async function sendSymptomMessage() {
    if (!symptomInput || !symptomInput.value.trim()) return;
    if (!chatSessionId) await startSymptomChat();
    
    const message = symptomInput.value.trim();
    addSymptomMessage('user', message);
    symptomInput.value = '';
    
    try {
        const response = await fetch(API_SYMPTOM_MESSAGE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: chatSessionId,
                message: message
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            addSymptomMessage('assistant', data.response || 'I understand. Can you tell me more?');
            
            // Display severity and specialist recommendations if available
            if (data.severity) {
                displaySymptomResults(data);
            }
        }
    } catch (err) {
        addSymptomMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        console.error('Chat error:', err);
    }
}

function addSymptomMessage(role, message) {
    if (!symptomChatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.innerHTML = `<div class="message-content">${message}</div>`;
    
    symptomChatMessages.appendChild(messageDiv);
    symptomChatMessages.scrollTop = symptomChatMessages.scrollHeight;
}

function displaySymptomResults(data) {
    if (!symptomResults) return;
    
    symptomResults.classList.remove('hidden');
    const lang = translations[currentLanguage] || translations.en || {};
    
    // Severity display
    const severityDiv = document.getElementById('symptom-severity');
    if (severityDiv && data.severity) {
        const severityConfig = {
            'high': { color: '#dc2626', bg: '#fee2e2', icon: 'fa-exclamation-triangle', message: lang.high_risk || 'High risk detected. Please consult a specialist soon.' },
            'medium': { color: '#ea580c', bg: '#ffedd5', icon: 'fa-exclamation-circle', message: lang.medium_risk || 'Medium risk detected. Consider consulting a healthcare professional.' },
            'low': { color: '#16a34a', bg: '#dcfce7', icon: 'fa-check-circle', message: lang.low_risk || 'No significant findings. Continue monitoring your health.' }
        };
        
        const config = severityConfig[data.severity] || severityConfig['low'];
        severityDiv.className = 'severity-card';
        severityDiv.innerHTML = `
            <div style="padding: 20px; background: ${config.bg}; border-left: 4px solid ${config.color}; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: ${config.color};">
                    <i class="fas ${config.icon}"></i> ${lang.severity || 'Severity'}: <span style="text-transform: uppercase;">${data.severity}</span>
                </h3>
                <p style="margin: 0; color: ${config.color}; font-weight: 500;">${config.message}</p>
            </div>
        `;
        severityDiv.classList.remove('hidden');
    }
    
    // Specialty recommendation
    const specialtyDiv = document.getElementById('symptom-specialty');
    if (specialtyDiv && data.specialty_display && (data.severity === 'high' || data.severity === 'medium')) {
        specialtyDiv.className = 'specialty-card';
        specialtyDiv.innerHTML = `
            <div style="padding: 15px; background: #f0f9ff; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin: 0 0 10px 0;"><i class="fas fa-user-md"></i> ${lang.recommended_specialty || 'Recommended Specialty'}</h4>
                <p style="margin: 0; font-size: 1.1em; font-weight: bold; color: #2563eb;">${data.specialty_display}</p>
            </div>
        `;
        specialtyDiv.classList.remove('hidden');
    }
    
    // Show geolocation only if severity >= medium
    if (data.severity === 'medium' || data.severity === 'high') {
        requestLocationForHospitals(data);
    }
}

function requestLocationForHospitals(data) {
    const lang = translations[currentLanguage] || translations.en || {};
    const hospitalsDiv = document.getElementById('symptom-hospitals');
    
    if (!hospitalsDiv) return;
    
    // Show location request with improved UI
    hospitalsDiv.className = 'hospitals-section';
    hospitalsDiv.innerHTML = `
        <div class="location-request-card">
            <h4><i class="fas fa-map-marker-alt"></i> ${lang.location_required || 'Location required to find nearby doctors.'}</h4>
            <p class="location-help-text">${lang.location_help || 'Choose how you want to share your location:'}</p>
            <div class="location-buttons">
                <button class="btn btn-primary" onclick="getGPSLocationForSymptoms()">
                    <i class="fas fa-crosshairs"></i> ${lang.use_gps || 'Use GPS Location'}
                </button>
                <button class="btn btn-secondary" onclick="openLocationModal('symptom')">
                    <i class="fas fa-map-pin"></i> ${lang.enter_manually || 'Enter Manually'}
                </button>
            </div>
        </div>
    `;
    hospitalsDiv.classList.remove('hidden');
}

// Make location functions globally available
window.getGPSLocationForSymptoms = function() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            findHospitalsForSymptoms(lat, lon);
        },
        (err) => {
            alert('Failed to get GPS location. Please enter your address manually.');
        },
        { enableHighAccuracy: true, timeout: 15000 }
    );
};

window.showAddressInputForSymptoms = function() {
    const inputDiv = document.getElementById('symptom-address-input');
    if (inputDiv) inputDiv.classList.remove('hidden');
};

// Location Modal Functions
let currentLocationContext = null; // 'symptom' or 'document'

window.openLocationModal = function(context) {
    currentLocationContext = context;
    const modal = document.getElementById('location-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        showLocationTab('gps');
    }
};

window.closeLocationModal = function() {
    const modal = document.getElementById('location-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    }
};

window.showLocationTab = function(tab) {
    document.querySelectorAll('.location-tab').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.location-input-section').forEach(section => section.classList.add('hidden'));
    
    if (tab === 'gps') {
        document.querySelector('.location-tab[onclick*="gps"]')?.classList.add('active');
        document.getElementById('gps-input-section')?.classList.remove('hidden');
    } else {
        document.querySelector('.location-tab[onclick*="address"]')?.classList.add('active');
        document.getElementById('address-input-section')?.classList.remove('hidden');
    }
};

window.submitGPSCoordinates = async function() {
    const latInput = document.getElementById('gps-lat');
    const lonInput = document.getElementById('gps-lon');
    
    if (!latInput || !lonInput) return;
    
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    
    // Validate coordinates
    if (isNaN(lat) || isNaN(lon)) {
        showNotification('Please enter valid coordinates', 'error');
        return;
    }
    
    if (lat < -90 || lat > 90) {
        showNotification('Latitude must be between -90 and 90', 'error');
        return;
    }
    
    if (lon < -180 || lon > 180) {
        showNotification('Longitude must be between -180 and 180', 'error');
        return;
    }
    
    closeLocationModal();
    showLoading();
    
    if (currentLocationContext === 'symptom') {
        await findHospitalsForSymptoms(lat, lon);
    } else {
        await findHospitalsForDocument(lat, lon);
    }
    
    hideLoading();
};

window.submitAddress = async function() {
    const addressInput = document.getElementById('address-input');
    if (!addressInput || !addressInput.value.trim()) {
        showNotification('Please enter an address', 'error');
        return;
    }
    
    const address = addressInput.value.trim();
    closeLocationModal();
    showLoading();
    
    try {
        // Geocode address via backend
        const response = await fetch(`${API_BASE}/agent/geocode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.lat && data.lon) {
                if (currentLocationContext === 'symptom') {
                    await findHospitalsForSymptoms(data.lat, data.lon);
                } else {
                    await findHospitalsForDocument(data.lat, data.lon);
                }
            } else {
                showNotification('Could not find location for this address', 'error');
            }
        } else {
            // Fallback: try direct geocoding
            const geocodeResponse = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`);
            if (geocodeResponse.ok) {
                const geoData = await geocodeResponse.json();
                if (geoData.length > 0) {
                    const lat = parseFloat(geoData[0].lat);
                    const lon = parseFloat(geoData[0].lon);
                    if (currentLocationContext === 'symptom') {
                        await findHospitalsForSymptoms(lat, lon);
                    } else {
                        await findHospitalsForDocument(lat, lon);
                    }
                } else {
                    showNotification('Address not found. Please try a different address.', 'error');
                }
            } else {
                showNotification('Failed to geocode address', 'error');
            }
        }
    } catch (err) {
        console.error('Geocoding error:', err);
        showNotification('Error processing address. Please try again.', 'error');
    }
    
    hideLoading();
};

// Sample symptom fill function
window.fillSymptomExample = function(text) {
    const input = document.getElementById('symptom-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Loading overlay
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

async function findHospitalsForSymptoms(lat, lon) {
    const lang = translations[currentLanguage] || translations.en || {};
    
    // Call geolocation endpoint
    try {
        const response = await fetch(`${API_BASE}/agent/geolocation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: 'Find nearby doctors',
                location: { lat, lon }
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayHospitalsForSymptoms(data.hospitals || [], { lat, lon });
        }
    } catch (err) {
        console.error('Error finding hospitals:', err);
    }
}

function displayHospitalsForSymptoms(hospitals, location) {
    const lang = translations[currentLanguage] || translations.en || {};
    const hospitalsDiv = document.getElementById('symptom-hospitals');
    const mapDiv = document.getElementById('symptom-map');
    
    if (!hospitalsDiv) return;
    
    if (hospitals.length > 0) {
        hospitalsDiv.innerHTML = `
            <h4 style="margin: 15px 0 10px 0;"><i class="fas fa-hospital"></i> ${lang.nearby_doctors || 'Nearby Doctors'}</h4>
            <div id="symptom-hospitals-list" class="hospitals-list"></div>
        `;
        
        const listDiv = document.getElementById('symptom-hospitals-list');
        hospitals.forEach((hospital, index) => {
            const card = document.createElement('div');
            card.className = 'hospital-card';
            card.innerHTML = `
                <h3><i class="fas fa-hospital"></i> ${index + 1}. ${hospital.name || 'Hospital'}</h3>
                <div class="hospital-info">
                    ${hospital.address ? `<div><i class="fas fa-map-marker-alt"></i> ${hospital.address}</div>` : ''}
                    ${hospital.distance_km !== undefined ? `<div><i class="fas fa-route"></i> ${hospital.distance_km.toFixed(2)} ${lang.km_away || 'km away'}</div>` : ''}
                    ${hospital.phone ? `<div><i class="fas fa-phone"></i> <a href="tel:${hospital.phone}">${hospital.phone}</a></div>` : ''}
                    ${hospital.specialty ? `<div><i class="fas fa-user-md"></i> ${hospital.specialty}</div>` : ''}
                </div>
                ${location ? `<a href="https://www.google.com/maps/dir/${location.lat},${location.lon}/${hospital.lat},${hospital.lon}" target="_blank" class="btn btn-primary btn-small" style="margin-top: 10px;">
                    <i class="fas fa-directions"></i> ${lang.get_directions || 'Get Directions'}
                </a>` : ''}
            `;
            listDiv.appendChild(card);
        });
        
        // Show map
        if (mapDiv && location) {
            mapDiv.classList.remove('hidden');
            initializeMap(location.lat, location.lon, hospitals, 'symptom-map');
        }
    } else {
        hospitalsDiv.innerHTML = `<p style="text-align: center; color: #666; padding: 20px;">${lang.no_hospitals || 'No hospitals found nearby.'}</p>`;
    }
}

// Document Upload Functions
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (fileInfo) {
        fileInfo.classList.remove('hidden');
        const lang = translations[currentLanguage] || translations.en || {};
        fileInfo.innerHTML = `<p><i class="fas fa-spinner fa-spin"></i> ${lang.uploading || 'Uploading'}... ${file.name}</p>`;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(API_OCR_ANALYZE, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            displayDocumentResults(data);
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(errorData.detail || 'Upload failed');
        }
    } catch (err) {
        if (fileInfo) {
            const lang = translations[currentLanguage] || translations.en || {};
            fileInfo.innerHTML = `<p><i class="fas fa-exclamation-circle"></i> ${lang.error || 'Error'}: ${err.message}</p>`;
        }
        console.error('Upload error:', err);
    }
}

function displayDocumentResults(data) {
    if (!documentResults) return;
    
    documentResults.classList.remove('hidden');
    const lang = translations[currentLanguage] || translations.en || {};
    
    const medicalAnalysis = data.medical_analysis || {};
    const severity = medicalAnalysis.severity || 'low';
    const findings = medicalAnalysis.findings || [];
    const recommendedSpecialty = medicalAnalysis.recommended_specialty;
    
    // Severity display
    const severityDiv = document.getElementById('document-severity');
    if (severityDiv) {
        const severityConfig = {
            'high': { color: '#dc2626', bg: '#fee2e2', icon: 'fa-exclamation-triangle', message: lang.high_risk || 'High risk detected.' },
            'medium': { color: '#ea580c', bg: '#ffedd5', icon: 'fa-exclamation-circle', message: lang.medium_risk || 'Medium risk detected.' },
            'low': { color: '#16a34a', bg: '#dcfce7', icon: 'fa-check-circle', message: lang.low_risk || 'No significant findings.' }
        };
        
        const config = severityConfig[severity] || severityConfig['low'];
        severityDiv.className = 'severity-card';
        severityDiv.innerHTML = `
            <div style="padding: 20px; background: ${config.bg}; border-left: 4px solid ${config.color}; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: ${config.color};">
                    <i class="fas ${config.icon}"></i> ${lang.severity || 'Severity'}: <span style="text-transform: uppercase;">${severity}</span>
                </h3>
                <p style="margin: 0; color: ${config.color}; font-weight: 500;">${config.message}</p>
            </div>
        `;
        severityDiv.classList.remove('hidden');
    }
    
    // Findings
    const findingsDiv = document.getElementById('document-findings');
    if (findingsDiv && findings.length > 0) {
        findingsDiv.className = 'findings-card';
        findingsDiv.innerHTML = `
            <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin: 0 0 10px 0;"><i class="fas fa-clipboard-list"></i> ${lang.findings || 'Findings'}</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    ${findings.map(f => `<li style="margin: 5px 0;">${f}</li>`).join('')}
                </ul>
            </div>
        `;
        findingsDiv.classList.remove('hidden');
    }
    
    // Specialty recommendation
    const specialtyDiv = document.getElementById('document-specialty');
    if (specialtyDiv && recommendedSpecialty && (severity === 'high' || severity === 'medium')) {
        specialtyDiv.className = 'specialty-card';
        specialtyDiv.innerHTML = `
            <div style="padding: 15px; background: #f0f9ff; border-radius: 8px; margin-top: 15px;">
                <h4 style="margin: 0 0 10px 0;"><i class="fas fa-user-md"></i> ${lang.recommended_specialty || 'Recommended Specialty'}</h4>
                <p style="margin: 0; font-size: 1.1em; font-weight: bold; color: #2563eb;">${recommendedSpecialty}</p>
            </div>
        `;
        specialtyDiv.classList.remove('hidden');
    }
    
    // Show hospitals only if severity >= medium
    if (severity === 'medium' || severity === 'high') {
        if (data.hospitals && data.hospitals.length > 0) {
            displayDocumentHospitals(data.hospitals, data.location_used);
        } else {
            requestLocationForDocument();
        }
    }
}

function requestLocationForDocument() {
    const lang = translations[currentLanguage] || translations.en || {};
    const hospitalsDiv = document.getElementById('document-hospitals');
    
    if (!hospitalsDiv) return;
    
    hospitalsDiv.className = 'hospitals-section';
    hospitalsDiv.innerHTML = `
        <div class="location-request-card">
            <h4><i class="fas fa-map-marker-alt"></i> ${lang.location_required || 'Location required to find nearby doctors.'}</h4>
            <p class="location-help-text">${lang.location_help || 'Choose how you want to share your location:'}</p>
            <div class="location-buttons">
                <button class="btn btn-primary" onclick="getGPSLocationForDocument()">
                    <i class="fas fa-crosshairs"></i> ${lang.use_gps || 'Use GPS Location'}
                </button>
                <button class="btn btn-secondary" onclick="openLocationModal('document')">
                    <i class="fas fa-map-pin"></i> ${lang.enter_manually || 'Enter Manually'}
                </button>
            </div>
        </div>
    `;
    hospitalsDiv.classList.remove('hidden');
}

window.getGPSLocationForDocument = function() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported.');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            findHospitalsForDocument(position.coords.latitude, position.coords.longitude);
        },
        (err) => {
            alert('Failed to get GPS location.');
        }
    );
};

// Close modal on outside click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('location-modal');
    if (modal && e.target === modal) {
        closeLocationModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeLocationModal();
    }
});

function displayDocumentHospitals(hospitals, location) {
    const lang = translations[currentLanguage] || translations.en || {};
    const hospitalsDiv = document.getElementById('document-hospitals');
    const mapDiv = document.getElementById('document-map');
    
    if (!hospitalsDiv) return;
    
    hospitalsDiv.className = 'hospitals-section';
    hospitalsDiv.innerHTML = `
        <h4 style="margin: 15px 0 10px 0;"><i class="fas fa-hospital"></i> ${lang.nearby_doctors || 'Nearby Doctors'}</h4>
        <div id="document-hospitals-list" class="hospitals-list"></div>
    `;
    
    const listDiv = document.getElementById('document-hospitals-list');
    hospitals.forEach((hospital, index) => {
        const card = document.createElement('div');
        card.className = 'hospital-card';
        card.innerHTML = `
            <h3><i class="fas fa-hospital"></i> ${index + 1}. ${hospital.name || 'Hospital'}</h3>
            <div class="hospital-info">
                ${hospital.address ? `<div><i class="fas fa-map-marker-alt"></i> ${hospital.address}</div>` : ''}
                ${hospital.distance_km !== undefined ? `<div><i class="fas fa-route"></i> ${hospital.distance_km.toFixed(2)} ${lang.km_away || 'km away'}</div>` : ''}
                ${hospital.phone ? `<div><i class="fas fa-phone"></i> <a href="tel:${hospital.phone}">${hospital.phone}</a></div>` : ''}
            </div>
            ${location ? `<a href="https://www.google.com/maps/dir/${location.lat},${location.lon}/${hospital.lat},${hospital.lon}" target="_blank" class="btn btn-primary btn-small">
                <i class="fas fa-directions"></i> ${lang.get_directions || 'Get Directions'}
            </a>` : ''}
        `;
        listDiv.appendChild(card);
    });
    
    if (mapDiv && location) {
        mapDiv.classList.remove('hidden');
        initializeMap(location.lat, location.lon, hospitals, 'document-map');
    }
}

async function findHospitalsForDocument(lat, lon) {
    try {
        const response = await fetch(API_GEOLOCATION, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: 'Find nearby doctors',
                location: { lat, lon }
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayDocumentHospitals(data.hospitals || [], { lat, lon });
        }
    } catch (err) {
        console.error('Error finding hospitals:', err);
    }
}

// Map initialization
function initializeMap(lat, lon, hospitals, mapContainerId) {
    const mapDiv = document.getElementById(mapContainerId);
    if (!mapDiv) return;
    
    if (map) map.remove();
    mapDiv.innerHTML = '';
    
    map = L.map(mapDiv).setView([lat, lon], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    L.marker([lat, lon], {
        icon: L.divIcon({
            className: 'user-marker',
            html: '<i class="fas fa-user" style="color: #2563eb; font-size: 24px;"></i>',
            iconSize: [24, 24]
        })
    }).addTo(map).bindPopup('<b>Your Location</b>').openPopup();
    
    markers = [];
    hospitals.forEach(hospital => {
        if (hospital.lat && hospital.lon) {
            const marker = L.marker([hospital.lat, hospital.lon], {
                icon: L.divIcon({
                    className: 'hospital-marker',
                    html: '<i class="fas fa-hospital" style="color: #dc2626; font-size: 24px;"></i>',
                    iconSize: [24, 24]
                })
            }).addTo(map);
            marker.bindPopup(`<b>${hospital.name || 'Hospital'}</b><br>${hospital.address || ''}`);
            markers.push(marker);
        }
    });
    
    if (hospitals.length > 0 && markers.length > 0) {
        const group = new L.featureGroup([...markers]);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Event Listeners
if (symptomInput) {
    symptomInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendSymptomMessage();
    });
}

if (sendSymptomBtn) {
    sendSymptomBtn.addEventListener('click', sendSymptomMessage);
}

if (fileInput) {
    fileInput.addEventListener('change', handleFileUpload);
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadTranslations);
} else {
    loadTranslations();
}
