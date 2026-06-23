// IndexedDB wrapper for image storage (replaces localStorage for large blobs)
const DB_NAME = 'smart_kv_db';
const DB_VERSION = 1;
const STORE_NAME = 'images';

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function saveImage(id, dataUrl) {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put({ id, dataUrl, savedAt: Date.now() });
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // Fallback to localStorage
    try { localStorage.setItem('smart_kv_img_' + id, dataUrl); } catch {}
    return false;
  }
}

export async function loadImage(id) {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).get(id);
    return new Promise((resolve) => {
      req.onsuccess = () => resolve(req.result?.dataUrl || null);
      req.onerror = () => {
        // Fallback to localStorage
        try { resolve(localStorage.getItem('smart_kv_img_' + id)); } catch { resolve(null); }
      };
    });
  } catch {
    try { return localStorage.getItem('smart_kv_img_' + id); } catch { return null; }
  }
}

export async function deleteImage(id) {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).delete(id);
    return new Promise((resolve) => {
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => resolve(false);
    });
  } catch {
    try { localStorage.removeItem('smart_kv_img_' + id); } catch {}
    return false;
  }
}

export async function getAllImageIds() {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).getAllKeys();
    return new Promise((resolve) => {
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });
  } catch {
    return [];
  }
}

// Migration: move any base64 images from localStorage to IndexedDB
export async function migrateFromLocalStorage() {
  const keys = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('smart_kv_') && !key.includes('img_')) {
      try {
        const val = JSON.parse(localStorage.getItem(key));
        // Check for large data (images stored as base64)
        const str = JSON.stringify(val);
        if (str.length > 50000) {
          // Extract image data and store in IndexedDB
          const imgId = key + '_img_' + Date.now();
          if (typeof val === 'object') {
            const images = extractImages(val);
            for (const img of images) {
              if (img.dataUrl && img.dataUrl.length > 10000) {
                await saveImage(imgId + '_' + img.key, img.dataUrl);
              }
            }
          }
        }
      } catch {}
    }
  }
  return true;
}

function extractImages(obj, prefix = '') {
  const results = [];
  if (!obj || typeof obj !== 'object') return results;
  for (const [key, val] of Object.entries(obj)) {
    if (typeof val === 'string' && val.startsWith('data:image') && val.length > 10000) {
      results.push({ key: prefix + key, dataUrl: val });
    } else if (typeof val === 'object' && val !== null) {
      results.push(...extractImages(val, prefix + key + '.'));
    }
  }
  return results;
}
