import { Stagehand } from '@browserbasehq/stagehand';
import { createStagehandLLMClient } from '../lib/ai-client';

/**
 * Example: Using custom OAuth-authenticated AI models with Stagehand
 * 
 * This demonstrates how to use your organization's custom AI models
 * instead of the default OpenAI/Anthropic models in browser automation.
 */
export async function runAutomationWithCustomAI(
  url: string,
  prompt: string,
  modelName: string = 'gpt-4'
) {
  // Create LLM client with your OAuth credentials
  const llmClient = await createStagehandLLMClient(modelName);

  // Initialize Stagehand with your custom AI model
  const stagehand = new Stagehand({
    env: "LOCAL",
    llmClient: llmClient,
    verbose: 1,
    localBrowserLaunchOptions: {
      headless: false,
    },
  });

  try {
    await stagehand.init();
    const page = stagehand.context.pages()[0];

    // Navigate to the target URL
    await page.goto(url, { waitUntil: "networkidle" });

    // All Stagehand operations now use your custom AI models
    const result = await stagehand.act(prompt);

    // Capture metrics
    const metrics = await stagehand.metrics;
    
    console.log('Automation completed successfully!');
    console.log('Tokens used:', (metrics?.totalPromptTokens || 0) + (metrics?.totalCompletionTokens || 0));
    
    await stagehand.close();
    
    return { success: true, result, metrics };
  } catch (error) {
    await stagehand.close().catch(() => {});
    throw error;
  }
}

/**
 * Example: Using observe + act pattern with custom AI models (2-3x faster)
 */
export async function runOptimizedAutomation(
  url: string,
  observePrompt: string,
  actPrompt: string,
  modelName: string = 'gpt-4'
) {
  const llmClient = await createStagehandLLMClient(modelName);

  const stagehand = new Stagehand({
    env: "LOCAL",
    llmClient: llmClient,
    verbose: 1,
    localBrowserLaunchOptions: {
      headless: false,
    },
  });

  try {
    await stagehand.init();
    const page = stagehand.context.pages()[0];

    await page.goto(url, { waitUntil: "networkidle" });

    // Best practice: observe() first to find elements
    const observed = await stagehand.observe(observePrompt);
    
    // Then act() on the observed elements (faster than direct act)
    if (Array.isArray(observed) && observed.length > 0) {
      const result = await stagehand.act(observed[0]);
      
      await stagehand.close();
      return { success: true, result, observed };
    }

    throw new Error('No elements found');
  } catch (error) {
    await stagehand.close().catch(() => {});
    throw error;
  }
}

/**
 * Example: Using agent mode with custom AI models for multi-step tasks
 */
export async function runAgentWithCustomAI(
  url: string,
  instruction: string,
  modelName: string = 'gpt-4'
) {
  const llmClient = await createStagehandLLMClient(modelName);

  const stagehand = new Stagehand({
    env: "LOCAL",
    llmClient: llmClient,
    verbose: 1,
    localBrowserLaunchOptions: {
      headless: false,
    },
  });

  try {
    await stagehand.init();
    const page = stagehand.context.pages()[0];

    await page.goto(url, { waitUntil: "networkidle" });

    // Create agent (it inherits the llmClient from Stagehand)
    const agent = stagehand.agent({
      systemPrompt: "You're a helpful automation assistant that can control a web browser.",
    });

    // Execute multi-step task
    const result = await agent.execute({
      instruction,
      maxSteps: 20,
    });

    const metrics = await stagehand.metrics;
    
    await stagehand.close();
    
    return { success: true, result, metrics };
  } catch (error) {
    await stagehand.close().catch(() => {});
    throw error;
  }
}
