/**
 * PaaS Platform - Main JavaScript Application
 * Handles client-side logic and API interactions
 */

// API Base URL
const API_BASE = '/api';

// Utility Functions
const utils = {
    /**
     * Format bytes to human-readable string
     */
    formatBytes: (bytes) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * Format memory in MB
     */
    formatMemory: (mb) => {
        if (mb < 1024) return `${mb} MB`;
        return `${(mb / 1024).toFixed(1)} GB`;
    },

    /**
     * Format date
     */
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    },

    /**
     * Show notification
     */
    notify: (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.style.position = 'fixed';
        notification.style.top = '100px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    /**
     * Debounce function
     */
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// API Client
const api = {
    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get frameworks
     */
    getFrameworks: () => api.request('/frameworks'),

    /**
     * Create deployment
     */
    createDeployment: (deploymentData) => api.request('/deploy', {
        method: 'POST',
        body: JSON.stringify(deploymentData),
    }),

    /**
     * Get all deployments
     */
    getDeployments: () => api.request('/deployments'),

    /**
     * Get deployment by ID
     */
    getDeployment: (id) => api.request(`/deployments/${id}`),

    /**
     * Delete deployment
     */
    deleteDeployment: (id) => api.request(`/deployments/${id}`, {
        method: 'DELETE',
    }),

    /**
     * Get deployment logs
     */
    getDeploymentLogs: (id) => api.request(`/deployments/${id}/logs`),

    /**
     * Get statistics
     */
    getStats: () => api.request('/stats'),
};

// Form Validation
const validation = {
    /**
     * Validate deployment name
     */
    deploymentName: (name) => {
        const pattern = /^[a-zA-Z0-9_-]{3,50}$/;
        return pattern.test(name);
    },

    /**
     * Validate GitHub URL
     */
    githubUrl: (url) => {
        const pattern = /^https?:\/\/github\.com\/[\w-]+\/[\w.-]+\/?$/;
        return pattern.test(url);
    },

    /**
     * Validate resources
     */
    resources: (resources, deploymentType) => {
        const limits = deploymentType === 'vm' ? {
            cores: { min: 1, max: 16 },
            memory: { min: 512, max: 32768 },
            disk: { min: 10, max: 500 }
        } : {
            cores: { min: 1, max: 8 },
            memory: { min: 256, max: 16384 },
            disk: { min: 5, max: 200 }
        };

        const errors = [];

        if (resources.cores < limits.cores.min || resources.cores > limits.cores.max) {
            errors.push(`Cores must be between ${limits.cores.min} and ${limits.cores.max}`);
        }

        if (resources.memory < limits.memory.min || resources.memory > limits.memory.max) {
            errors.push(`Memory must be between ${limits.memory.min} and ${limits.memory.max} MB`);
        }

        if (resources.disk < limits.disk.min || resources.disk > limits.disk.max) {
            errors.push(`Disk must be between ${limits.disk.min} and ${limits.disk.max} GB`);
        }

        return errors;
    }
};

// Animation helpers
const animations = {
    /**
     * Fade in element
     */
    fadeIn: (element, duration = 300) => {
        element.style.opacity = '0';
        element.style.display = 'block';

        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            element.style.opacity = Math.min(progress / duration, 1);

            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    },

    /**
     * Fade out element
     */
    fadeOut: (element, duration = 300) => {
        let start = null;
        const initialOpacity = parseFloat(window.getComputedStyle(element).opacity);

        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            element.style.opacity = initialOpacity * (1 - progress / duration);

            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };

        requestAnimationFrame(animate);
    }
};

// Export for use in other scripts
window.PaaSPlatform = {
    utils,
    api,
    validation,
    animations
};

// Initialize smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading class to body when page loads
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});

console.log('PaaS Platform Client Initialized');
