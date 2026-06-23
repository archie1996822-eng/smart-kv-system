import { useState, useCallback, useRef } from 'react';

export function useUndoRedo(initialState, maxHistory = 50) {
  const [history, setHistory] = useState([initialState]);
  const [index, setIndex] = useState(0);
  const skipNextRef = useRef(false);

  const current = history[index];

  const pushState = useCallback((newState) => {
    if (skipNextRef.current) {
      skipNextRef.current = false;
      return;
    }
    setHistory(prev => {
      const trimmed = prev.slice(0, index + 1);
      const next = [...trimmed, newState];
      if (next.length > maxHistory) next.shift();
      return next;
    });
    setIndex(prev => Math.min(prev + 1, maxHistory - 1));
  }, [index, maxHistory]);

  const undo = useCallback(() => {
    setIndex(prev => Math.max(0, prev - 1));
  }, []);

  const redo = useCallback(() => {
    setIndex(prev => Math.min(history.length - 1, prev + 1));
  }, [history.length]);

  const replaceCurrent = useCallback((newState) => {
    skipNextRef.current = true;
    setHistory(prev => {
      const next = [...prev];
      next[index] = newState;
      return next;
    });
  }, [index]);

  const canUndo = index > 0;
  const canRedo = index < history.length - 1;

  return { current, pushState, undo, redo, replaceCurrent, canUndo, canRedo, historyLength: history.length };
}
