import { StatusBar } from '../StatusBar';

export default function StatusBarExample() {
  return (
    <div className="p-6">
      <div className="space-y-2">
        <StatusBar 
          connectionStatus="connected"
          browserVersion="Chromium 131.0"
          executionTime="2.5s"
        />
        <StatusBar 
          connectionStatus="connecting"
          browserVersion="Chromium 131.0"
        />
        <StatusBar 
          connectionStatus="disconnected"
          browserVersion="Chromium 131.0"
        />
      </div>
    </div>
  );
}
