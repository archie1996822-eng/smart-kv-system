// Unified Storage Layer
// Layer 1: localStorage (metadata, <100KB per key)
// Layer 2: IndexedDB (images, large blobs, unlimited*)
// Layer 3: Supabase (cloud sync, optional, requires credentials)

const DB_NAME = 'miketv_db';
const DB_VERSION = 2;

// --- IndexedDB ---
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('images')) {
        db.createObjectStore('images', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('blobs')) {
        db.createObjectStore('blobs', { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// Save large data to IndexedDB
export async function saveBlob(id, data) {
  try {
    const db = await openDB();
    const tx = db.transaction('blobs', 'readwrite');
    tx.objectStore('blobs').put({ id, data, savedAt: Date.now() });
    return new Promise((resolve) => { tx.oncomplete = () => resolve(true); tx.onerror = () => resolve(false); });
  } catch { return false; }
}

export async function loadBlob(id) {
  try {
    const db = await openDB();
    const tx = db.transaction('blobs', 'readonly');
    const req = tx.objectStore('blobs').get(id);
    return new Promise((resolve) => { req.onsuccess = () => resolve(req.result?.data || null); req.onerror = () => resolve(null); });
  } catch { return null; }
}

// --- Storage Quota ---
export function getStorageInfo() {
  let used = 0;
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith('smart_kv_')) used += (localStorage.getItem(key) || '').length;
  }
  const total = 5 * 1024 * 1024; // 5MB localStorage limit
  return {
    used,
    total,
    usedKB: (used / 1024).toFixed(1),
    totalKB: (total / 1024).toFixed(0),
    pct: ((used / total) * 100).toFixed(1),
    isWarning: used > total * 0.8,
    isCritical: used > total * 0.95,
  };
}

// --- Export / Import ---
export function exportAllData() {
  const data = {};
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith('smart_kv_')) {
      try { data[key] = JSON.parse(localStorage.getItem(key)); } catch { data[key] = localStorage.getItem(key); }
    }
  }
  return data;
}

export function importAllData(jsonData) {
  let count = 0;
  for (const [key, value] of Object.entries(jsonData)) {
    if (key.startsWith('smart_kv_')) {
      try {
        localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value));
        count++;
      } catch {}
    }
  }
  return count;
}

// --- Auto-cleanup ---
export function cleanupOldData(maxAgeDays = 90) {
  const cutoff = Date.now() - maxAgeDays * 24 * 60 * 60 * 1000;
  let cleaned = 0;
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (!key?.startsWith('smart_kv_')) continue;
    try {
      const val = JSON.parse(localStorage.getItem(key));
      const time = val?.createdAt || val?.savedAt || val?.updatedAt;
      if (time && new Date(time).getTime() < cutoff) {
        localStorage.removeItem(key);
        cleaned++;
      }
    } catch {}
  }
  return cleaned;
}

// --- Supabase Sync Status ---
import { isSupabaseConfigured } from './supabase';

export function getBackendStatus() {
  return {
    localStorage: { available: true, ...getStorageInfo() },
    indexedDB: { available: 'indexedDB' in window },
    supabase: { available: isSupabaseConfigured() },
  };
}
