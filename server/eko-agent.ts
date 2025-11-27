import { Eko, type LLMs, type Agent } from '@eko-ai/eko';
import { BrowserAgent } from '@eko-ai/eko-nodejs';

export interface StepData {
  id: string;
  type: 'thinking' | 'browsing' | 'extracting' | 'writing' | 'success' | 'error';
  message: string;
  detail?: string;
  timestamp: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

const DEFAULT_MODEL_STR = "claude-sonnet-4-20250514";

let ekoInstance: Eko | null = null;
let browserAgent: BrowserAgent | null = null;

export async function initializeEko(): Promise<Eko> {
  if (ekoInstance) return ekoInstance;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable is not set. Please add your Anthropic API key in the Secrets tab.');
  }

  const llms: LLMs = {
    default: {
      provider: "anthropic",
      model: DEFAULT_MODEL_STR,
      apiKey,
      config: {
        baseURL: "https://api.anthropic.com/v1",
      },
    }
  };

  browserAgent = new BrowserAgent();
  const agents: Agent[] = [browserAgent];

  ekoInstance = new Eko({
    llms,
    agents,
  });

  return ekoInstance;
}

export async function cleanupEko(): Promise<void> {
  browserAgent = null;
  ekoInstance = null;
}

export async function executeAutomation(
  prompt: string,
  onStep?: (step: StepData) => void
): Promise<{ success: boolean; result?: string; error?: string }> {
  let stepCounter = 0;
  
  const emitStep = (type: StepData['type'], message: string, detail?: string, status: StepData['status'] = 'running') => {
    const step: StepData = {
      id: `step-${stepCounter++}-${Date.now()}`,
      type,
      message,
      detail,
      timestamp: Date.now(),
      status,
    };
    onStep?.(step);
  };

  try {
    emitStep('thinking', 'Initializing Eko agent...', 'Loading browser automation environment');
    
    const eko = await initializeEko();
    
    emitStep('thinking', 'Analyzing prompt...', `Task: "${prompt}"`);
    emitStep('thinking', 'Planning workflow', 'AI is generating execution plan...');
    
    emitStep('browsing', 'Executing automation', 'Browser agent is running the task...');
    
    const result = await eko.run(prompt);
    
    const resultText = typeof result === 'string' 
      ? result 
      : result?.result 
        ? String(result.result) 
        : 'Task completed';
    
    emitStep('success', 'Task completed successfully', resultText, 'completed');
    
    await cleanupEko();
    
    return {
      success: true,
      result: resultText,
    };
  } catch (error: any) {
    const errorMessage = error.message || 'Unknown error occurred';
    
    emitStep('error', 'Execution failed', errorMessage, 'failed');
    
    await cleanupEko();
    
    return {
      success: false,
      error: errorMessage,
    };
  }
}
