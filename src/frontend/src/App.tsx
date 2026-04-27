import { RagProvider } from './context/RagContext';
import { DesktopProvider } from './context/DesktopContext';
import { Desktop } from './components/Desktop';
import WindowWrapper from './components/WindowWrapper';
import ChatApp from './components/ChatApp';
import RagMonitorApp from './components/RagMonitorApp';
import ExplorerApp from './components/ExplorerApp';
import NotepadApp from './components/NotepadApp';
import PdfReaderApp from './components/PdfReaderApp';

function App() {
  return (
    <DesktopProvider>
      <RagProvider>
        <Desktop>
          
          <WindowWrapper id="chat" defaultWidth="350px">
            <ChatApp />
          </WindowWrapper>
          
          <WindowWrapper id="ragMonitor" defaultWidth="500px">
            <RagMonitorApp />
          </WindowWrapper>

          <WindowWrapper id="explorer" defaultWidth="450px">
            <ExplorerApp />
          </WindowWrapper>

          <WindowWrapper id="notepad" defaultWidth="400px">
            <NotepadApp />
          </WindowWrapper>
          
          <WindowWrapper id="pdfReader" defaultWidth="600px" defaultHeight="500px">
            <PdfReaderApp />
          </WindowWrapper>

        </Desktop>
      </RagProvider>
    </DesktopProvider>
  );
}

export default App;
