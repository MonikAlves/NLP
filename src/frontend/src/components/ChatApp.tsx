import { useState, useRef, useEffect } from 'react';
import { useRag } from '../context/RagContext';
import { useDesktop } from '../context/DesktopContext';

const ChatApp = () => {
  const { 
    messages, isProcessing, setIsProcessing, setCurrentStep, 
    setCurrentQuery, addMessage, apiResponse, setApiResponse, setDebugInfo 
  } = useRag();
  const { windows } = useDesktop();
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    const query = inputText;
    
    // 1. Mostrar mensagem do usuário imediatamente
    addMessage({
      id: Date.now().toString(),
      sender: 'user',
      text: query
    });
    setCurrentQuery(query);
    setInputText('');
    setIsProcessing(true); // Começa a mostrar o status de processamento
    setApiResponse('');    // Reseta resposta anterior

    const monitorState = windows['ragMonitor'];
    const isMonitorVisible = monitorState && monitorState.isOpen && !monitorState.isMinimized;

    try {
      // 2. Chamar a API via PROXY (para evitar CORS no local)
      const url = new URL(window.location.origin + '/api-nlp/ask');
      url.searchParams.append('pergunta', query);
      url.searchParams.append('debug', isMonitorVisible.toString());

      const response = await fetch(url.toString(), { 
        method: 'GET',
        headers: {
          'accept': 'application/json'
        }
      });

      const data = await response.json();
      
      console.log("Retorno da API NLP Delta:", data);
      console.log("Monitor visível?", isMonitorVisible);

      const respostaFinal = data.resposta || "API respondida (ver log)";
      setApiResponse(respostaFinal);

      // Processa informações de debug se disponíveis
      if (data.debug) {
        setDebugInfo(data.debug);
        // Note: setFoundDocs foi removido daqui para ser disparado 
        // no passo a passo do monitor.
      } else {
        setDebugInfo(null);
      }

      if (isMonitorVisible) {
        // Monitor está aberto: inicia processo visual
        setIsProcessing(true);
        setCurrentStep('QUERY_DISPLAY');
        
        // Opcional: Adiciona um log no próprio chat informando que o processo começou
        console.log("Iniciando animação passo a passo no monitor...");
      } else {
        // Monitor fechado: exibe resposta direta
        addMessage({
          id: Date.now().toString(),
          sender: 'ia',
          text: respostaFinal
        });
        setIsProcessing(false);
      }
    } catch (error) {
      console.error("Erro ao conectar com a API:", error);
      setIsProcessing(false);
      
      addMessage({
        id: Date.now().toString(),
        sender: 'ia',
        text: `(Erro) Não foi possível conectar à API. Verifique o console.`
      });
    }
  };

  const formatMessage = (text: string) => {
    // Converte **negrito**
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Converte listas simples (* ou -)
    formatted = formatted.replace(/^\* (.*)/gm, '<li>$1</li>');
    formatted = formatted.replace(/^- (.*)/gm, '<li>$1</li>');
    
    // Envolve grupos de <li> em <ul> se necessário, ou apenas deixa os line breaks
    // Para simplificar no Win95, vamos apenas usar <br/> e manter o estilo limpo
    return formatted.split('\n').map((line, i) => (
      <span key={i}>
        <span dangerouslySetInnerHTML={{ __html: line }} />
        <br />
      </span>
    ));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="sunken-panel chat-messages" style={{ flex: 1, padding: '8px' }}>
        {messages.map((m) => (
          <div key={m.id} className={`message ${m.sender}`} style={{ marginBottom: '12px' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '2px', color: m.sender === 'user' ? '#ffffffff' : '#800000' }}>
              {m.sender === 'user' ? 'Você:' : 'IA:'}
            </div>
            <div style={{ paddingLeft: '8px', borderLeft: m.sender === 'ia' ? '2px solid #808080' : 'none' }}>
              {formatMessage(m.text)}
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="message ia" style={{ opacity: 0.7 }}>
            <strong>IA:</strong> 
            <div style={{ paddingLeft: '8px', fontStyle: 'italic' }}>
              {apiResponse ? 'Resposta pronta! Siga os passos no RAG Monitor para visualizar.' : 'Processando consulta... aguarde um momento.'}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={isProcessing}
          style={{ flex: 1 }}
          placeholder="Digite sua mensagem..."
        />
        <button type="submit" disabled={isProcessing || !inputText.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
};

export default ChatApp;
