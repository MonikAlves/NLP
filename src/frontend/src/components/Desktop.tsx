import React, { type ReactNode } from 'react';
import Taskbar from './Taskbar';
import { useDesktop } from '../context/DesktopContext';
import chatIcon from '../assets/computer_with_programs_alpha.png';
import ragIcon from '../assets/files_from_computer_alpha.png';
import explorerIcon from '../assets/folder_hi-res_alpha.png';
import notepadIcon from '../assets/Notepad.png';
import pdfIcon from '../assets/web-documents_alpha.png';

const iconMap: Record<string, string> = {
  chat: chatIcon,
  ragMonitor: ragIcon,
  explorer: explorerIcon,
  notepad: notepadIcon,
  pdfReader: pdfIcon,
};

export const Desktop = ({ children }: { children: ReactNode }) => {
  const { windows, openWindow, focusWindow } = useDesktop();

  const handleDoubleClick = (id: string) => {
    openWindow(id);
    focusWindow(id);
  };

  return (
    <div className="desktop" style={{ alignItems: 'flex-start', justifyContent: 'flex-start', alignContent: 'flex-start' }}>
      {/* Container de ícones da Área de Trabalho */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '35px', paddingTop: '20px', zIndex: 1, paddingLeft: '10px' }}>
        {Object.values(windows).map(w => (
          <div 
            key={w.id} 
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer', width: '100px', textAlign: 'center', color: '#fff' }}
            onDoubleClick={() => handleDoubleClick(w.id)}
          >
            <img 
              src={iconMap[w.id]} 
              alt={w.title} 
              style={{ width: '64px', height: '64px', marginBottom: '8px', imageRendering: 'pixelated' }} 
            />
            <span style={{ fontSize: '14px', textShadow: '1px 1px 0 #000', fontWeight: 'bold' }}>{w.title}</span>
          </div>
        ))}
      </div>

      {children}
      <Taskbar />
    </div>
  );
};
