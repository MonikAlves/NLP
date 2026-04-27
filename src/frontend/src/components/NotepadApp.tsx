import React from 'react';
import { useRag } from '../context/RagContext';
import { useDesktop } from '../context/DesktopContext';

const NotepadApp = () => {
  const { activeDoc, setPdfUrl } = useRag();
  const { openWindow, focusWindow } = useDesktop();

  const handleLinkClick = (url: string) => {
    setPdfUrl(url);
    openWindow('pdfReader');
    focusWindow('pdfReader');
  };

  const renderContent = () => {
    if (!activeDoc) return null;
    
    // Expressão regular simples para detectar URLs
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = activeDoc.content.split(urlRegex);

    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <span 
            key={index} 
            className="notepad-link"
            style={{ color: '#0000ee', textDecoration: 'underline', cursor: 'pointer' }}
            onClick={() => handleLinkClick(part)}
          >
            link
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff' }}>
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #808080', padding: '4px', background: '#c0c0c0', color: '#000' }}>
        <span>File</span>
        <span>Edit</span>
        <span>Search</span>
        <span>Help</span>
      </div>
      <div 
        className="sunken-panel"
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          fontFamily: '"Courier New", Courier, monospace', 
          padding: '8px', 
          whiteSpace: 'pre-wrap',
          background: '#fff',
          color: '#000'
        }}
      >
        <div style={{ marginBottom: '15px' }}>{renderContent()}</div>
        
        {activeDoc?.pdfUrl && (
          <div style={{ borderTop: '1px solid #c0c0c0', paddingTop: '8px', marginTop: '16px' }}>
            <strong>[Link para PDF]: </strong>
            <span 
              className="notepad-link"
              onClick={() => handleLinkClick(activeDoc.pdfUrl!)}
            >
              {activeDoc.filename.split(' (')[0]}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotepadApp;
