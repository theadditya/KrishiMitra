const CACHE_NAME = 'smart-farmer-v3'; // Increment this version
const ASSETS = [
    '/static/style.css',
    '/static/signup.css',
    '/static/app.js',
    '/static/manifest.json',
    '/static/1.png',
    '/static/icons/icon-144x144.png',
    // Do NOT cache '/', '/dashboard', or '/register' HTML here. 
    // We want those to always be fresh from the server.
];

self.addEventListener('install', event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.map(key => {
                if (key !== CACHE_NAME) return caches.delete(key);
            })
        ))
    );
    return self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // 1. IGNORE API CALLS (Login, Signup, etc.) - Always go to network
    if (event.request.method !== 'GET' || url.pathname.startsWith('/login') || url.pathname.startsWith('/signup')) {
        return; 
    }

    // 2. NETWORK FIRST strategy for HTML pages (Dashboard, Home, etc.)
    // This ensures the user always gets the latest page (and correct redirects)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(event.request)) // Fallback to cache only if offline
        );
        return;
    }

    // 3. CACHE FIRST for static assets (CSS, JS, Images)
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});