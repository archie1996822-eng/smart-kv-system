import { createContext, useContext, useState, useEffect } from 'react';

const THEME_KEY = 'smart_kv_theme';

export const ThemeContext = createContext(null);
export const useTheme = () => useContext(ThemeContext);

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    try { return localStorage.getItem(THEME_KEY) || 'light'; } catch { return 'light'; }
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('app-dark');
    } else {
      root.classList.remove('app-dark');
    }
    try { localStorage.setItem(THEME_KEY, theme); } catch {}
  }, [theme]);

  const toggleTheme = () => setThemeState(t => t === 'dark' ? 'light' : 'dark');
  const setTheme = (t) => setThemeState(t);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
