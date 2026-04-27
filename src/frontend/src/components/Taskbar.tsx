import React, { useState } from 'react';
import { useDesktop } from '../context/DesktopContext';
import chatIcon from '../assets/computer_with_programs_alpha.png';
import ragIcon from '../assets/files_from_computer_alpha.png';
import explorerIcon from '../assets/folder_hi-res_alpha.png';
import notepadIcon from '../assets/Notepad.png';
import startIcon from '../assets/start.png';
import pdfIcon from '../assets/web-documents_alpha.png';


const iconMap: Record<string, string> = {
  chat: chatIcon,
  notepad: notepadIcon,
  explorer: explorerIcon,
  ragMonitor: ragIcon,
  pdfReader: pdfIcon,
};

const Clock = () => {
  const [time, setTime] = React.useState(new Date());

  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      padding: '2px 6px',
      boxShadow: 'inset -1px -1px #fff, inset 1px 1px #0a0a0a, inset -2px -2px #dfdfdf, inset 2px 2px #808080',
      fontSize: '12px',
      height: '22px'
    }}>
      <span style={{ marginTop: '2px' }}>
        {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()}
      </span>
    </div>
  );
};

const Taskbar = () => {
  const { windows, toggleMinimize, openWindow, focusWindow } = useDesktop();
  const [startOpen, setStartOpen] = useState(false);

  const handleStartMenuClick = (id: string) => {
    openWindow(id);
    focusWindow(id);
    setStartOpen(false);
  };

  return (
    <div className="taskbar" style={{ position: 'absolute', bottom: 0, left: 0, right: 0, display: 'flex', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
        <div style={{ position: 'relative' }}>
          <button 
            className={`start-button ${startOpen ? 'active' : ''}`}
            onClick={() => setStartOpen(!startOpen)}
          >
            <img src={startIcon} alt="logo" style={{ width: '16px', height: '16px' }} />
            Start
          </button>
          
          {startOpen && (
            <div className="window" style={{ 
              position: 'absolute', 
              bottom: '100%', 
              left: 0, 
              width: '200px', 
              display: 'flex', 
              flexDirection: 'column',
              marginBottom: '2px',
              zIndex: 9999
            }}>
              <div style={{ padding: '2px', background: '#000080', color: '#fff', fontWeight: 'bold' }}>
                Windows 95
              </div>
              <div className="window-body" style={{ margin: 0, padding: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {Object.values(windows).map(w => (
                  <button 
                    key={w.id} 
                    style={{ textAlign: 'left', padding: '6px', border: 'none', background: 'transparent', width: '100%', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
                    onClick={() => handleStartMenuClick(w.id)}
                  >
                    <img src={iconMap[w.id]} alt="" style={{ width: '24px', height: '24px', imageRendering: 'pixelated' }} />
                    {w.title}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{ width: '2px', height: '100%', background: '#808080', borderRight: '1px solid #fff', margin: '0 4px' }}></div>

        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          {Object.values(windows).map(w => {
            if (!w.isOpen) return null;
            return (
              <button 
                key={w.id}
                className={`taskbar-item ${!w.isMinimized ? 'active' : ''}`}
                onClick={() => toggleMinimize(w.id)}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{w.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', paddingRight: '2px', gap: '4px' }}>
        <div style={{ width: '2px', height: '18px', background: '#808080', borderRight: '1px solid #fff' }}></div>
        <Clock />
      </div>
    </div>
  );
};

export default Taskbar;
