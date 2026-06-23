// Supabase integration layer — ready to connect
// Install: npm install @supabase/supabase-js
// Configure: set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

let supabaseClient = null;

export async function getSupabase() {
  if (!SUPABASE_URL || !SUPABASE_KEY) return null;
  if (supabaseClient) return supabaseClient;
  try {
    const { createClient } = await import('@supabase/supabase-js');
    supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);
    return supabaseClient;
  } catch {
    return null;
  }
}

export function isSupabaseConfigured() {
  return !!(SUPABASE_URL && SUPABASE_KEY);
}

// Database schema (for reference — run in Supabase SQL editor):
/*
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  display_name TEXT,
  avatar TEXT,
  role TEXT DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  name TEXT NOT NULL,
  description TEXT,
  type TEXT DEFAULT 'image', -- 'image' | 'video'
  status TEXT DEFAULT 'active',
  thumbnail_url TEXT,
  material_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE generations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  user_id UUID REFERENCES profiles(id),
  material_id TEXT,
  image_url TEXT,
  video_url TEXT,
  prompt_text TEXT,
  quality TEXT,
  status TEXT DEFAULT 'done',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  generation_id UUID REFERENCES generations(id),
  user_id UUID REFERENCES profiles(id),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  image_url TEXT,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
*/

// Storage adapter — sync when Supabase is configured
export async function syncToCloud(key, data) {
  const sb = await getSupabase();
  if (!sb) return false;
  // Cloud sync implementation when connected
  return false;
}

export async function loadFromCloud(key) {
  const sb = await getSupabase();
  if (!sb) return null;
  return null;
}
