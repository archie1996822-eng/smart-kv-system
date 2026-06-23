// Browser Notification API wrapper + in-app notification queue

let permissionGranted = false;

export async function requestNotificationPermission() {
  if (!('Notification' in window)) return false;
  if (Notification.permission === 'granted') { permissionGranted = true; return true; }
  if (Notification.permission === 'denied') return false;
  const result = await Notification.requestPermission();
  permissionGranted = result === 'granted';
  return permissionGranted;
}

export function sendBrowserNotification(title, options = {}) {
  if (!permissionGranted || !('Notification' in window)) return;
  try {
    new Notification(title, {
      icon: '/favicon.svg',
      badge: '/favicon.svg',
      ...options,
    });
  } catch {}
}

// Check if browser supports notifications
export function isNotificationSupported() {
  return 'Notification' in window;
}

export function getPermissionStatus() {
  if (!('Notification' in window)) return 'unsupported';
  return Notification.permission;
}

// In-app notification queue for background tasks
const taskListeners = new Set();

export function notifyTaskUpdate(task) {
  taskListeners.forEach(fn => fn(task));
}

export function subscribeToTasks(fn) {
  taskListeners.add(fn);
  return () => taskListeners.delete(fn);
}

// Background task tracker
const backgroundTasks = new Map();

export function startBackgroundTask(id, name, totalItems) {
  const task = { id, name, totalItems, completed: 0, failed: 0, status: 'running', startedAt: Date.now() };
  backgroundTasks.set(id, task);
  notifyTaskUpdate(task);
  return task;
}

export function updateBackgroundTask(id, { completed, failed, status }) {
  const task = backgroundTasks.get(id);
  if (!task) return;
  if (completed !== undefined) task.completed = completed;
  if (failed !== undefined) task.failed = failed;
  if (status) task.status = status;
  notifyTaskUpdate(task);
  if (status === 'done' || status === 'failed') {
    sendBrowserNotification(
      status === 'done' ? '任务完成！' : '任务失败',
      { body: `${task.name}: ${task.completed}/${task.totalItems} 完成`, tag: id }
    );
  }
}

export function getBackgroundTasks() {
  return Array.from(backgroundTasks.values());
}
