import { RecordingIndicator } from '../RecordingIndicator';

export default function RecordingIndicatorExample() {
  return (
    <div className="p-6 h-screen relative">
      <p className="text-sm text-muted-foreground">Recording indicator appears in the top-right corner</p>
      <RecordingIndicator 
        isRecording={true}
        onStop={() => console.log('Stop recording')}
      />
    </div>
  );
}
