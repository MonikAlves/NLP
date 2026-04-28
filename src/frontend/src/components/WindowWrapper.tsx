import React, { type ReactNode, useState, useRef, useEffect } from 'react';
import { useDesktop } from '../context/DesktopContext';

interface WindowWrapperProps {
  id: string;
  children: ReactNode;
  defaultWidth?: string;
  defaultHeight?: string;
}

const WindowWrapper = ({ id, children, defaultWidth = '400px', defaultHeight = '450px' }: WindowWrapperProps) => {
  const { windows, closeWindow, minimizeWindow, toggleMaximize, focusWindow, updatePosition, updateSize } = useDesktop();
  const windowState = windows[id];

  const [localPos, setLocalPos] = useState({ 
    x: window.innerWidth > 600 ? Math.max(20, (window.innerWidth - parseInt(defaultWidth)) / 2 + (Math.random() * 40 - 20)) : 5, 
    y: window.innerWidth > 600 ? Math.max(20, (window.innerHeight - parseInt(defaultHeight)) / 2 + (Math.random() * 40 - 20)) : 5
  });
  const [localSize, setLocalSize] = useState({ 
    width: Math.min(window.innerWidth - 10, parseInt(defaultWidth)), 
    height: Math.min(window.innerHeight - 60, parseInt(defaultHeight)) 
  });
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  
  const dragRef = useRef<{ startX: number; startY: number; initialX: number; initialY: number } | null>(null);
  const resizeRef = useRef<{ startX: number; startY: number; initialW: number; initialH: number } | null>(null);

  useEffect(() => {
    if (windowState?.position) {
      setLocalPos(windowState.position);
    }
  }, [windowState?.position]);

  useEffect(() => {
    if (windowState?.size) {
      setLocalSize(windowState.size);
    }
  }, [windowState?.size]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && dragRef.current) {
        const dx = e.clientX - dragRef.current.startX;
        const dy = e.clientY - dragRef.current.startY;
        setLocalPos({
          x: dragRef.current.initialX + dx,
          y: dragRef.current.initialY + dy,
        });
      } else if (isResizing && resizeRef.current) {
        const dx = e.clientX - resizeRef.current.startX;
        const dy = e.clientY - resizeRef.current.startY;
        
        const newWidth = Math.max(250, resizeRef.current.initialW + dx);
        const newHeight = Math.max(150, resizeRef.current.initialH + dy);
        
        setLocalSize({
          width: newWidth,
          height: newHeight,
        });
      }
    };

    const handleMouseUp = () => {
      if (isDragging && dragRef.current) {
        setIsDragging(false);
        updatePosition(id, localPos.x, localPos.y);
      }
      if (isResizing && resizeRef.current) {
        setIsResizing(false);
        updateSize(id, localSize.width, localSize.height);
      }
    };

    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, isResizing, localPos, localSize, id, updatePosition, updateSize]);

  if (!windowState || !windowState.isOpen || windowState.isMinimized) {
    return null;
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    focusWindow(id);
    if (windowState.isMaximized) return;
    setIsDragging(true);
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      initialX: localPos.x,
      initialY: localPos.y,
    };
  };

  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    focusWindow(id);
    if (windowState.isMaximized) return;
    setIsResizing(true);
    resizeRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      initialW: localSize.width,
      initialH: localSize.height,
    };
  };

  const style: React.CSSProperties = windowState.isMaximized ? {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: '30px', 
    width: 'auto',
    height: 'auto',
    zIndex: windowState.zIndex,
    display: 'flex',
    flexDirection: 'column'
  } : {
    position: 'absolute',
    top: `${localPos.y}px`,
    left: `${localPos.x}px`,
    width: `${localSize.width}px`,
    height: `${localSize.height}px`,
    zIndex: windowState.zIndex,
    display: 'flex',
    flexDirection: 'column',
    cursor: isDragging ? 'grabbing' : 'default'
  };

  return (
    <div className="window" style={style} onMouseDown={() => focusWindow(id)}>
      <div 
        className="title-bar" 
        onMouseDown={handleMouseDown} 
        style={{ cursor: windowState.isMaximized ? 'default' : (isDragging ? 'grabbing' : 'grab') }}
      >
        <div className="title-bar-text">{windowState.title}</div>
        <div className="title-bar-controls">
          <button aria-label="Minimize" onClick={(e) => { e.stopPropagation(); minimizeWindow(id); }}></button>
          <button aria-label="Maximize" onClick={(e) => { e.stopPropagation(); toggleMaximize(id); }}></button>
          <button aria-label="Close" onClick={(e) => { e.stopPropagation(); closeWindow(id); }}></button>
        </div>
      </div>
      <div className="window-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', margin: '8px', overflow: 'hidden', position: 'relative' }}>
        {children}
      </div>

      {/* Resize handle (canto inferior direito) */}
      {!windowState.isMaximized && (
        <div 
          style={{ 
            position: 'absolute', 
            bottom: '2px', 
            right: '2px', 
            width: '12px', 
            height: '12px', 
            cursor: 'nwse-resize', 
            zIndex: 1000,
            background: `url("data:image/svg+xml,%3Csvg width='12' height='12' viewBox='0 0 12 12' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 0L0 11M11 4L4 11M11 8L8 11' stroke='white' stroke-width='1'/%3E%3Cpath d='M12 0L0 12M12 4L4 12M12 8L8 12' stroke='%23808080' stroke-width='1'/%3E%3C/svg%3E") no-repeat bottom right`,
            imageRendering: 'pixelated'
          }} 
          onMouseDown={handleResizeMouseDown}
        />
      )}
    </div>
  );
};

export default WindowWrapper;
