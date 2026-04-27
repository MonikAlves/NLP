import { useRag } from '../context/RagContext';
import { useDesktop } from '../context/DesktopContext';

const ExplorerApp = () => {
  const { foundDocs, setActiveDoc } = useRag();
  const { openWindow, focusWindow } = useDesktop();

  const handleOpenDoc = (doc: any) => {
    setActiveDoc(doc);
    openWindow('notepad');
    focusWindow('notepad');
  };

  return (
    <div style={{ display: 'flex', height: '100%', background: '#fff' }}>
      <div style={{ width: '120px', borderRight: '1px solid #808080', background: '#c0c0c0', padding: '4px' }}>
        <strong>C:\\RAG_Docs\\</strong>
      </div>
      <div className="sunken-panel" style={{ flex: 1, padding: '8px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignContent: 'flex-start' }}>
        {foundDocs.length === 0 ? (
          <div style={{ color: '#808080' }}>Nenhum documento recuperado ainda. Realize uma busca no RAG.</div>
        ) : (
          foundDocs.map(doc => (
            <div 
              key={doc.id} 
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer', width: '80px', textAlign: 'center' }}
              onDoubleClick={() => handleOpenDoc(doc)}
            >
              {/* Ícone simples de texto */}
              <div style={{ width: '32px', height: '40px', background: '#fff', border: '1px solid #000', position: 'relative', marginBottom: '4px' }}>
                 <div style={{ position: 'absolute', top: 0, right: 0, borderBottom: '8px solid #c0c0c0', borderLeft: '8px solid #000', width: 0, height: 0 }}></div>
                 <div style={{ padding: '8px 4px' }}>
                   <div style={{ borderBottom: '1px solid #000', marginBottom: '2px' }}></div>
                   <div style={{ borderBottom: '1px solid #000', marginBottom: '2px' }}></div>
                   <div style={{ borderBottom: '1px solid #000', marginBottom: '2px' }}></div>
                 </div>
              </div>
              <span style={{ fontSize: '12px' }}>{doc.filename}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ExplorerApp;
