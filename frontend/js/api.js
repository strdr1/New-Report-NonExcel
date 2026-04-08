const API_BASE = '/api';

const API = {
    // Profiles
    async getProfiles() {
        const response = await fetch(`${API_BASE}/profiles`);
        return response.json();
    },
    
    async createProfile(data) {
        const response = await fetch(`${API_BASE}/profiles`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async getProfile(id) {
        const response = await fetch(`${API_BASE}/profiles/${id}`);
        return response.json();
    },
    
    async updateProfile(id, data) {
        const response = await fetch(`${API_BASE}/profiles/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async deleteProfile(id) {
        const response = await fetch(`${API_BASE}/profiles/${id}`, {
            method: 'DELETE'
        });
        return response.json();
    },
    
    // Years
    async getYears(profileId) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years`);
        return response.json();
    },
    
    async createYear(profileId, year) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({year})
        });
        return response.json();
    },
    
    async getYear(profileId, year) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}`);
        return response.json();
    },
    
    async updateYear(profileId, year, data) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async deleteYear(profileId, year) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}`, {
            method: 'DELETE'
        });
        return response.json();
    },
    
    // Months
    async getMonths(profileId, year) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}/months`);
        return response.json();
    },
    
    async getMonth(profileId, year, month) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}/months/${month}`);
        return response.json();
    },
    
    async getReport(profileId, year, month) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}/months/${month}/report`);
        return response.json();
    },
    
    async updateMonth(profileId, year, month, data) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}/months/${month}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    },

    // Daily records
    async updateDailyRecord(profileId, year, month, day, data) {
        const response = await fetch(`${API_BASE}/profiles/${profileId}/years/${year}/months/${month}/days/${day}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    }
};
