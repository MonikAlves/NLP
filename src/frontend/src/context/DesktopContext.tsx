import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface WindowState {
  id: string;
  title: string;
  isOpen: boolean;
  isMinimized: boolean;
  isMaximized: boolean;
  zIndex: number;
  position?: { x: number, y: number };
  size?: { width: number, height: number };
}

interface DesktopContextType {
  windows: Record<string, WindowState>;
  openWindow: (id: string) => void;
  closeWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  restoreWindow: (id: string) => void;
  toggleMinimize: (id: string) => void;
  toggleMaximize: (id: string) => void;
  focusWindow: (id: string) => void;
  isWindowVisible: (id: string) => boolean;
  updatePosition: (id: string, x: number, y: number) => void;
  updateSize: (id: string, width: number, height: number) => void;
}

const initialWindows: Record<string, WindowState> = {
  chat: { id: 'chat', title: 'Chat.exe', isOpen: false, isMinimized: false, isMaximized: false, zIndex: 1, position: { x: 50, y: 50 }, size: { width: 350, height: 450 } },
  ragMonitor: { id: 'ragMonitor', title: 'RAG.exe', isOpen: false, isMinimized: false, isMaximized: false, zIndex: 2, position: { x: 600, y: 50 }, size: { width: 500, height: 450 } },
  explorer: { id: 'explorer', title: 'Explorer.exe', isOpen: false, isMinimized: false, isMaximized: false, zIndex: 3, position: { x: 300, y: 150 }, size: { width: 450, height: 450 } },
  notepad: { id: 'notepad', title: 'Notepad.exe', isOpen: false, isMinimized: false, isMaximized: false, zIndex: 4, position: { x: 400, y: 200 }, size: { width: 400, height: 450 } },
  pdfReader: { id: 'pdfReader', title: 'PdfReader.exe', isOpen: false, isMinimized: false, isMaximized: false, zIndex: 5, position: { x: 100, y: 100 }, size: { width: 600, height: 500 } },
};

const DesktopContext = createContext<DesktopContextType | undefined>(undefined);

export const DesktopProvider = ({ children }: { children: ReactNode }) => {
  const [windows, setWindows] = useState<Record<string, WindowState>>(initialWindows);
  const [maxZIndex, setMaxZIndex] = useState(10);

  const focusWindow = (id: string) => {
    setMaxZIndex(prev => {
      const nextZ = prev + 1;
      setWindows(prevWindows => ({
        ...prevWindows,
        [id]: { ...prevWindows[id], zIndex: nextZ }
      }));
      return nextZ;
    });
  };

  const openWindow = (id: string) => {
    setMaxZIndex(prev => {
      const nextZ = prev + 1;
      setWindows(prevWindows => ({
        ...prevWindows,
        [id]: { ...prevWindows[id], isOpen: true, isMinimized: false, zIndex: nextZ }
      }));
      return nextZ;
    });
  };

  const closeWindow = (id: string) => {
    setWindows(prev => ({
      ...prev,
      [id]: { ...prev[id], isOpen: false }
    }));
  };

  const minimizeWindow = (id: string) => {
    setWindows(prev => ({
      ...prev,
      [id]: { ...prev[id], isMinimized: true }
    }));
  };

  const restoreWindow = (id: string) => {
    setMaxZIndex(prev => {
      const nextZ = prev + 1;
      setWindows(prevWindows => ({
        ...prevWindows,
        [id]: { ...prevWindows[id], isMinimized: false, zIndex: nextZ }
      }));
      return nextZ;
    });
  };

  const toggleMinimize = (id: string) => {
    if (windows[id].isMinimized) {
      restoreWindow(id);
    } else {
      minimizeWindow(id);
    }
  };

  const toggleMaximize = (id: string) => {
    setMaxZIndex(prev => {
      const nextZ = prev + 1;
      setWindows(prevWindows => ({
        ...prevWindows,
        [id]: { ...prevWindows[id], isMaximized: !prevWindows[id].isMaximized, isMinimized: false, zIndex: nextZ }
      }));
      return nextZ;
    });
  };

  const isWindowVisible = (id: string) => {
    const w = windows[id];
    return w && w.isOpen && !w.isMinimized;
  };

  const updatePosition = (id: string, x: number, y: number) => {
    setWindows(prev => ({
      ...prev,
      [id]: { ...prev[id], position: { x, y } }
    }));
  };

  const updateSize = (id: string, width: number, height: number) => {
    setWindows(prev => ({
      ...prev,
      [id]: { ...prev[id], size: { width, height } }
    }));
  };

  return (
    <DesktopContext.Provider value={{
      windows, openWindow, closeWindow, minimizeWindow, restoreWindow,
      toggleMinimize, toggleMaximize, focusWindow, isWindowVisible, updatePosition, updateSize
    }}>
      {children}
    </DesktopContext.Provider>
  );
};

export const useDesktop = () => {
  const context = useContext(DesktopContext);
  if (!context) throw new Error('useDesktop must be used within DesktopProvider');
  return context;
};

