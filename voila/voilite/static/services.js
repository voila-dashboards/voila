// This is the service worker with the Cache-first network
const CACHE = 'precache';

// Communication channel for drive access
const broadcast = new BroadcastChannel('/api/drive.v1');

self.addEventListener('install', (event) => {
  self.skipWaiting();

  event.waitUntil(
    caches.open(CACHE).then((cache) => {
      // this is where we should (try to) add all relevant files
      return cache.addAll([]);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', async (event) => {
  const url = new URL(event.request.url);

  if (url.origin === location.origin && url.pathname.includes('/api/drive')) {
    // Forward request to main using the broadcast channel
    event.respondWith(
      new Promise(async (resolve) => {
        broadcast.onmessage = (event) => {
          resolve(new Response(JSON.stringify(event.data)));
        };
        broadcast.postMessage(await event.request.json());
      })
    );
    return;
  }

  if (
    event.request.method !== 'GET' ||
    event.request.url.match(/^http/) === null ||
    url.pathname.includes('/api/')
  ) {
    return;
  }

  event.respondWith(
    fromCache(event.request).then(
      (response) => {
        // The response was found in the cache so we respond with it and update the entry
        // This is where we call the server to get the newest version of the
        // file to use the next time we show view
        event.waitUntil(
          fetch(event.request).then((response) => {
            return updateCache(event.request, response);
          })
        );

        return response;
      },
      () => {
        // The response was not found in the cache so we look for it on the server
        return fetch(event.request).then((response) => {
          // If request was success, add or update it in the cache
          event.waitUntil(updateCache(event.request, response.clone()));

          return response;
        });
      }
    )
  );
});

function fromCache(request) {
  // Check to see if you have it in the cache
  // Return response
  // If not in the cache, then return
  return caches.open(CACHE).then((cache) => {
    return cache.match(request).then((matching) => {
      if (!matching || matching.status === 404) {
        return Promise.reject('no-match');
      }
      return matching;
    });
  });
}

function updateCache(request, response) {
  return caches.open(CACHE).then((cache) => {
    return cache.put(request, response);
  });
}
