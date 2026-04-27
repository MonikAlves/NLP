import React from 'react';
import { useRag } from '../context/RagContext';

const PdfReaderApp = () => {
  const { pdfUrl } = useRag();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#808080' }}>
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #808080', padding: '4px', background: '#c0c0c0', color: '#000' }}>
        <span>File</span>
        <span>View</span>
        <span>Help</span>
      </div>
      
      <div className="sunken-panel" style={{ flex: 1, background: '#fff', position: 'relative' }}>
        {pdfUrl ? (
          <iframe 
            src={`https://docs.google.com/viewer?url=${encodeURIComponent(pdfUrl)}&embedded=true`} 
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="PDF Reader"
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#808080' }}>
            Nenhum documento carregado.
          </div>
        )}
      </div>
      
      <div style={{ padding: '2px 4px', fontSize: '12px', background: '#c0c0c0', borderTop: '1px solid #dfdfdf', display: 'flex', justifyContent: 'space-between', color: '#000' }}>
        <span>{pdfUrl ? 'Visualizando PDF' : 'Pronto'}</span>
        <span>100%</span>
      </div>
    </div>
  );
};

export default PdfReaderApp;
