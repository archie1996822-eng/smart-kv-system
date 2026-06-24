// Supabase Integration Layer
// To enable: set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env
// Run the SQL schema below in your Supabase SQL editor

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://gkihbgfzqooqrzigjjem.supabase.co';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_IZsvQcW2kdtTGUjR2lScEA_G4GLjcmo';

let supabaseClient = null;
let initAttempted = false;

export function isSupabaseConfigured() {
  return !!(SUPABASE_URL && SUPABASE_KEY);
}

export function getSupabaseConfig() {
  return {
    configured: isSupabaseConfigured(),
    url: SUPABASE_URL ? SUPABASE_URL.substring(0, 20) + '...' : '(未配置)',
    status: isSupabaseConfigured() ? '已配置' : '未配置 — 设置环境变量后启用',
  };
}

export async function getClient() {
  if (supabaseClient) return supabaseClient;
  if (!isSupabaseConfigured()) return null;
  try {
    const { createClient } = await import('@supabase/supabase-js');
    supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);
    return supabaseClient;
  } catch (e) {
    console.warn('Supabase client init failed:', e.message);
    return null;
  }
}

// Sync functions — call these when Supabase is configured
export async function syncProject(project) {
  const sb = await getClient();
  if (!sb) return null;
  const { data, error } = await sb.from('projects').upsert({
    id: project.id,
    name: project.name,
    description: project.description,
    type: project.type || 'image',
    status: project.status || 'active',
    thumbnail_url: project.thumbnailUrl,
    material_count: project.materialCount,
    updated_at: new Date().toISOString(),
  }).select();
  if (error) console.warn('Supabase sync error:', error.message);
  return data;
}

export async function syncGeneration(generation) {
  const sb = await getClient();
  if (!sb) return null;
  const { data, error } = await sb.from('generations').upsert({
    id: generation.id,
    project_id: generation.projectId,
    material_id: generation.materialId,
    image_url: generation.imageUrl,
    prompt_text: generation.promptText,
    quality: generation.quality,
    status: generation.status || 'done',
    created_at: new Date().toISOString(),
  }).select();
  if (error) console.warn('Supabase sync error:', error.message);
  return data;
}

export async function loadUserProjects() {
  const sb = await getClient();
  if (!sb) return [];
  const { data } = await sb.from('projects').select('*').order('updated_at', { ascending: false }).limit(50);
  return data || [];
}

// Test connection
export async function testConnection() {
  if (!isSupabaseConfigured()) return { ok: false, error: 'URL 或 Key 未配置' };
  const sb = await getClient();
  if (!sb) return { ok: false, error: '客户端初始化失败' };
  try {
    const { count, error } = await sb.from('projects').select('*', { count: 'exact', head: true });
    if (error) return { ok: false, error: error.message };
    return { ok: true, message: `连接成功，当前 ${count} 个项目` };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// Sync a project to Supabase
export async function cloudSyncProject(project) {
  const sb = await getClient();
  if (!sb) return false;
  const { error } = await sb.from('projects').upsert({
    id: project.id,
    name: project.name,
    description: project.description || '',
    type: project.type || 'image',
    status: project.status || 'active',
    thumbnail_url: project.thumbnailUrl || null,
    material_count: project.materialCount || 0,
    updated_at: new Date().toISOString(),
  });
  return !error;
}

// Sync a generation to Supabase
export async function cloudSyncGeneration(gen) {
  const sb = await getClient();
  if (!sb) return false;
  const { error } = await sb.from('generations').upsert({
    id: gen.id || 'gen_' + Date.now(),
    project_id: gen.projectId || null,
    material_id: gen.materialId || null,
    image_url: gen.imageUrl || null,
    video_url: gen.videoUrl || null,
    prompt_text: gen.promptText || null,
    quality: gen.quality || 'B',
    status: gen.status || 'done',
    created_at: gen.createdAt || new Date().toISOString(),
  });
  return !error;
}

// Load projects from Supabase
export async function cloudLoadProjects() {
  const sb = await getClient();
  if (!sb) return [];
  const { data, error } = await sb.from('projects').select('*').order('updated_at', { ascending: false }).limit(50);
  if (error) return [];
  return data || [];
}

// SQL Schema (run in Supabase SQL Editor):
/*
-- Profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  display_name TEXT,
  avatar TEXT,
  role TEXT DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES profiles(id),
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  type TEXT DEFAULT 'image',
  status TEXT DEFAULT 'active',
  thumbnail_url TEXT,
  material_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Generations
CREATE TABLE IF NOT EXISTS generations (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES profiles(id),
  material_id TEXT,
  image_url TEXT,
  video_url TEXT,
  prompt_text TEXT,
  quality TEXT DEFAULT 'B',
  status TEXT DEFAULT 'done',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Comments
CREATE TABLE IF NOT EXISTS comments (
  id TEXT PRIMARY KEY,
  generation_id TEXT REFERENCES generations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES profiles(id),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Favorites
CREATE TABLE IF NOT EXISTS favorites (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES profiles(id),
  image_url TEXT NOT NULL,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, image_url)
);

-- Enable Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for now, tighten in production)
CREATE POLICY "Allow all" ON projects FOR ALL USING (true);
CREATE POLICY "Allow all" ON generations FOR ALL USING (true);
CREATE POLICY "Allow all" ON comments FOR ALL USING (true);
CREATE POLICY "Allow all" ON favorites FOR ALL USING (true);
*/
