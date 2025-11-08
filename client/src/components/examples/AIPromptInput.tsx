import { AIPromptInput } from '../AIPromptInput';

export default function AIPromptInputExample() {
  return (
    <div className="p-6 max-w-2xl">
      <AIPromptInput 
        onGenerate={(prompt) => console.log('Generate automation:', prompt)}
      />
    </div>
  );
}
