// CONFIGURATION
// Change this to your backend URL

// For local development (when running frontend locally)
// const API_BASE = 'http://localhost:8000/api';

// For production (when frontend is on Vercel, backend on your Linux)
// Option 1: Your public IP with port forwarding
// const API_BASE = 'http://YOUR_PUBLIC_IP:8000/api';

// Option 2: Using ngrok (recommended)
// const API_BASE = 'https://YOUR_NGROK_URL.ngrok.io/api';

// Option 3: Using a domain with reverse proxy
// const API_BASE = 'https://api.yourdomain.com/api';

// SET YOUR BACKEND URL HERE:
// Using ngrok for HTTPS access (works from anywhere):
const API_BASE = 'https://0b74-2001-16a2-cc19-7000-b72e-b8b3-f06d-7a42.ngrok-free.app/api';

// For remote access from anywhere, use ngrok:
// 1. Run: ngrok http 8000
// 2. Replace URL below with your ngrok URL (e.g., https://abc123.ngrok.io/api)
// const API_BASE = 'https://YOUR_NGROK_URL.ngrok.io/api';

// Don't change below this line
const CONFIG = {
    API_BASE: API_BASE,
    TOKEN_KEY: 'deal_curator_token',
    DEFAULT_LOGIN: {
        username: 'admin',
        password: 'admin123'
    }
};
