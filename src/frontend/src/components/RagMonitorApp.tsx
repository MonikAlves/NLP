import React, { useEffect, useRef } from 'react';
import { useRag } from '../context/RagContext';
import { useDesktop } from '../context/DesktopContext';

const mockEmbeddings = "[0.0123, -0.5432, 0.9981, -0.1122, 0.3341, ...]";
const mockDocs = `[DOC 1]: O React é uma biblioteca JavaScript declarativa, eficiente e flexível para criar interfaces de usuário.\n[DOC 2]: Permite compor UIs complexas a partir de pequenos e isolados pedaços de código chamados "componentes".`;

const RagMonitorApp = () => {
  const { currentStep, advanceStep, currentQuery, debugInfo } = useRag();
  const { openWindow, focusWindow } = useDesktop();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
    
    // Abre o Explorer automaticamente ao chegar no passo 4
    if (currentStep === 'DOCS_OPENED') {
      openWindow('explorer');
      focusWindow('explorer');
    }
  }, [currentStep, openWindow, focusWindow]);

  const embeddingPreview = Array.isArray(debugInfo?.embedding_da_pergunta?.embedding_preview)
    ? `[${debugInfo.embedding_da_pergunta.embedding_preview.join(', ')}, ...]`
    : mockEmbeddings;

  const documentosArray = debugInfo?.documentos_retriever;
  
  const searchPreview = Array.isArray(documentosArray)
    ? `Total de arquivos encontrados: ${documentosArray.length}\n` + 
      documentosArray.map((d: any) => `- ${d?.name || '?'}: Score ${d?.score || '0'}`).join('\n')
    : `Total de arquivos encontrados: 2\n- doc_react.txt: Score 0.95\n- doc_hooks.txt: Score 0.88`;

  const openedPreview = Array.isArray(documentosArray)
    ? `Arquivos abertos na janela:\n` + 
      documentosArray.map((d: any) => `> ${d?.name || '?'}`).join('\n')
    : `Arquivos abertos na janela:\n> doc_react.txt\n> doc_hooks.txt`;

  if (currentStep === 'IDLE') {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div className="sunken-panel rag-monitor-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div>Aguardando nova consulta... <span className="blink">_</span></div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="sunken-panel rag-monitor-content">
        {/* Passo 1: Pergunta */}
        {['QUERY_DISPLAY', 'EMBEDDING_GEN', 'VECTOR_SEARCH', 'DOCS_OPENED', 'PROMPT_ASSEMBLY', 'IA_RESPONSE'].includes(currentStep) && (
          <div className="rag-step">
            <div className="rag-step-title">&gt; 1. PERGUNTA RECEBIDA</div>
            <div className="rag-step-data">Query: "{currentQuery}"</div>
          </div>
        )}

        {/* Passo 2: Embedding */}
        {['EMBEDDING_GEN', 'VECTOR_SEARCH', 'DOCS_OPENED', 'PROMPT_ASSEMBLY', 'IA_RESPONSE'].includes(currentStep) && (
          <div className="rag-step">
            <div className="rag-step-title">&gt; 2. GERANDO EMBEDDINGS (Dimensões: {debugInfo?.embedding_da_pergunta?.dimension || 1536})</div>
            <div className="rag-step-data text-muted" style={{ fontSize: '11px', wordBreak: 'break-all' }}>{embeddingPreview}</div>
          </div>
        )}

        {/* Passo 3: Busca/Arquivos */}
        {['VECTOR_SEARCH', 'DOCS_OPENED', 'PROMPT_ASSEMBLY', 'IA_RESPONSE'].includes(currentStep) && (
          <div className="rag-step">
            <div className="rag-step-title">&gt; 3. BUSCA VETORIAL NO DB</div>
            <div className="rag-step-data text-muted" style={{ fontSize: '11px', whiteSpace: 'pre-wrap' }}>{searchPreview}</div>
          </div>
        )}

        {/* Passo 4: Arquivos Abertos */}
        {['DOCS_OPENED', 'PROMPT_ASSEMBLY', 'IA_RESPONSE'].includes(currentStep) && (
          <div className="rag-step">
            <div className="rag-step-title">&gt; 4. ABRINDO DOCUMENTOS</div>
            <div className="rag-step-data text-muted" style={{ fontSize: '11px', whiteSpace: 'pre-wrap' }}>{openedPreview}</div>
          </div>
        )}

        {/* Passo 5: Prompt */}
        {['PROMPT_ASSEMBLY', 'IA_RESPONSE'].includes(currentStep) && (
          <div className="rag-step">
            <div className="rag-step-title">&gt; 5. MONTAGEM DO PROMPT FINAL</div>
            <div className="rag-step-data text-muted" style={{ fontSize: '11px', whiteSpace: 'pre-wrap' }}>
              Prompt Final montado com os chunks acima para envio ao LLM.
            </div>
          </div>
        )}

        {currentStep !== 'IA_RESPONSE' && (
          <div className="rag-step">
            <div className="rag-step-data"><span className="blink">Aguardando confirmação do usuário..._</span></div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="rag-controls">
        <button onClick={advanceStep} style={{ width: '100%', fontWeight: 'bold' }}>
          {currentStep === 'PROMPT_ASSEMBLY' ? 'Gerar Resposta Final >' : 'Continuar Passo a Passo >'}
        </button>
      </div>
    </div>
  );
};

export default RagMonitorApp;
