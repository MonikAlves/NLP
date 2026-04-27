import { createContext, useContext, useState, type ReactNode } from 'react';

export type RagStep = 'IDLE' | 'QUERY_DISPLAY' | 'EMBEDDING_GEN' | 'VECTOR_SEARCH' | 'DOCS_OPENED' | 'PROMPT_ASSEMBLY' | 'IA_RESPONSE';

export interface Message {
  id: string;
  sender: 'user' | 'ia';
  text: string;
}

export interface Document {
  id: string;
  filename: string;
  content: string;
  pdfUrl?: string;
}

interface RagContextType {
  messages: Message[];
  addMessage: (msg: Message) => void;
  currentStep: RagStep;
  setCurrentStep: (step: RagStep) => void;
  isProcessing: boolean;
  setIsProcessing: (val: boolean) => void;
  currentQuery: string;
  setCurrentQuery: (q: string) => void;
  advanceStep: () => void;
  foundDocs: Document[];
  setFoundDocs: (docs: Document[]) => void;
  activeDoc: Document | null;
  setActiveDoc: (doc: Document | null) => void;
  pdfUrl: string | null;
  setPdfUrl: (url: string | null) => void;
  apiResponse: string | null;
  setApiResponse: (res: string | null) => void;
  debugInfo: any | null;
  setDebugInfo: (info: any | null) => void;
}

const RagContext = createContext<RagContextType | undefined>(undefined);

export const mockDocsData: Document[] = [
  { id: '1', filename: 'doc_react.txt', content: 'O React é uma biblioteca JavaScript declarativa, eficiente e flexível para criar interfaces de usuário. Ele permite compor UIs complexas a partir de pequenos e isolados pedaços de código chamados "componentes".' },
  { id: '2', filename: 'doc_hooks.txt', content: 'Hooks são uma nova adição ao React 16.8. Eles permitem que você use o state e outros recursos do React sem escrever uma classe.' },
  { id: '3', filename: 'doc_aneel.txt', content: 'Despacho nº 3.386/2016 da ANEEL. Este documento trata de decisões regulatórias.\n\nLink para o documento original:\nhttp://www2.aneel.gov.br/cedoc/ndsp20163386.pdf', pdfUrl: 'http://www2.aneel.gov.br/cedoc/ndsp20163386.pdf' }
];

export const RagProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'ia', text: 'Olá! Sou um assistente RAG rodando no Windows 95. Como posso ajudar?' }
  ]);
  const [currentStep, setCurrentStep] = useState<RagStep>('IDLE');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  
  // Para o Explorer
  const [foundDocs, setFoundDocs] = useState<Document[]>([]);
  const [activeDoc, setActiveDoc] = useState<Document | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<any | null>(null);

  const addMessage = (msg: Message) => {
    setMessages(prev => [...prev, msg]);
  };

  const advanceStep = () => {
    switch (currentStep) {
      case 'QUERY_DISPLAY':
        setCurrentStep('EMBEDDING_GEN');
        break;
      case 'EMBEDDING_GEN':
        setCurrentStep('VECTOR_SEARCH');
        break;
      case 'VECTOR_SEARCH':
        // Quando avança para o passo 4, os arquivos já devem "aparecer" no Explorer
        if (debugInfo && debugInfo.documentos_retriever) {
          const mappedDocs = debugInfo.documentos_retriever.map((d: any) => ({
            id: d?.id || Math.random().toString(),
            filename: `${d?.name || 'documento'} (${String(d?.id || '').substring(0, 8)})`,
            content: d?.chunk || '',
            pdfUrl: d?.name ? `http://www2.aneel.gov.br/cedoc/${d.name}` : null
          }));
          setFoundDocs(mappedDocs);
        } else if (foundDocs.length === 0) {
          setFoundDocs(mockDocsData);
        }
        setCurrentStep('DOCS_OPENED');
        break;
      case 'DOCS_OPENED':
        setCurrentStep('PROMPT_ASSEMBLY');
        break;
      case 'PROMPT_ASSEMBLY':
        setCurrentStep('IA_RESPONSE');
        break;
      case 'IA_RESPONSE':
        addMessage({
          id: Date.now().toString(),
          sender: 'ia',
          text: apiResponse || `Baseado nos documentos, aqui está a resposta para "${currentQuery}".`
        });
        setCurrentStep('IDLE');
        setIsProcessing(false);
        setCurrentQuery('');
        setFoundDocs([]); // Limpa para a próxima
        break;
      default:
        break;
    }
  };

  return (
    <RagContext.Provider value={{
      messages,
      addMessage,
      currentStep,
      setCurrentStep,
      isProcessing,
      setIsProcessing,
      currentQuery,
      setCurrentQuery,
      advanceStep,
      foundDocs,
      setFoundDocs,
      activeDoc,
      setActiveDoc,
      pdfUrl,
      setPdfUrl,
      apiResponse,
      setApiResponse,
      debugInfo,
      setDebugInfo
    }}>
      {children}
    </RagContext.Provider>
  );
};

export const useRag = () => {
  const context = useContext(RagContext);
  if (!context) throw new Error('useRag must be used within RagProvider');
  return context;
};
