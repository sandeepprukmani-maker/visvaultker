import chalk from 'chalk';
import * as readline from 'readline';
import { PlaywrightMCPClient } from './mcp-client.js';
import { interpretPrompt, summarizeResults } from './llm.js';
import * as fs from 'fs';
import * as path from 'path';

interface AutomationOptions {
  headless?: boolean;
  screenshotPath?: string;
}

function checkOpenAIKey(): void {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('OPENAI_API_KEY environment variable is not set. Please set it to use this tool.');
  }
}

async function saveScreenshot(result: unknown, screenshotPath: string): Promise<boolean> {
  try {
    if (result && typeof result === 'object' && 'content' in result) {
      const content = (result as { content: Array<{ type: string; data?: string; mimeType?: string }> }).content;
      if (Array.isArray(content)) {
        const imageContent = content.find(c => c.type === 'image');
        if (imageContent && imageContent.data) {
          const dir = path.dirname(screenshotPath);
          if (dir && dir !== '.') {
            fs.mkdirSync(dir, { recursive: true });
          }
          const imageBuffer = Buffer.from(imageContent.data, 'base64');
          fs.writeFileSync(screenshotPath, imageBuffer);
          console.log(chalk.green(`  ✓ Screenshot saved to: ${screenshotPath}`));
          return true;
        }
      }
    }
  } catch (error) {
    console.error(chalk.yellow(`  ⚠ Could not save screenshot: ${error instanceof Error ? error.message : error}`));
  }
  return false;
}

export async function automateWithPrompt(
  prompt: string,
  options: AutomationOptions = {}
): Promise<void> {
  checkOpenAIKey();
  
  const client = new PlaywrightMCPClient();

  try {
    await client.connect(options.headless);
    const tools = client.getTools();

    if (tools.length === 0) {
      throw new Error('No tools available from MCP server');
    }

    const actions: string[] = [];
    const results: string[] = [];
    let done = false;
    let iterations = 0;
    const maxIterations = 20;
    let screenshotTaken = false;

    while (!done && iterations < maxIterations) {
      iterations++;
      console.log(chalk.blue(`\n--- Step ${iterations} ---`));

      const lastResult = results.length > 0 ? results[results.length - 1] : undefined;
      const response = await interpretPrompt(prompt, tools, actions, lastResult);

      console.log(chalk.yellow(`Thinking: ${response.thinking}`));

      if (response.done) {
        done = true;
        console.log(chalk.green(`\n✅ Task completed!`));
        if (response.summary) {
          console.log(chalk.white(`Summary: ${response.summary}`));
        }
        break;
      }

      if (response.toolCalls.length === 0) {
        console.log(chalk.yellow('No tool calls returned, task may be complete.'));
        done = true;
        break;
      }

      for (const toolCall of response.toolCalls) {
        try {
          const result = await client.callTool(toolCall.name, toolCall.arguments);
          const actionDescription = `${toolCall.name}(${JSON.stringify(toolCall.arguments)})`;
          actions.push(actionDescription);

          let resultText = 'Success';
          if (result && typeof result === 'object' && 'content' in result) {
            const content = (result as { content: Array<{ type: string; text?: string }> }).content;
            if (Array.isArray(content)) {
              const textContent = content.find(c => c.type === 'text');
              if (textContent && textContent.text) {
                resultText = textContent.text.substring(0, 500);
              }
            }
          }
          results.push(resultText);

          if (toolCall.name === 'browser_take_screenshot' && options.screenshotPath) {
            screenshotTaken = await saveScreenshot(result, options.screenshotPath);
          }
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          results.push(`Error: ${errorMsg}`);
          console.error(chalk.red(`Tool call failed: ${errorMsg}`));
        }
      }
    }

    if (iterations >= maxIterations) {
      console.log(chalk.yellow(`\n⚠️ Reached maximum iterations (${maxIterations})`));
    }

    if (options.screenshotPath && !screenshotTaken) {
      console.log(chalk.blue('\n📸 Taking final screenshot...'));
      try {
        const screenshotResult = await client.callTool('browser_take_screenshot', {});
        await saveScreenshot(screenshotResult, options.screenshotPath);
        actions.push('browser_take_screenshot({})');
        results.push('Screenshot captured');
      } catch (error) {
        console.error(chalk.yellow(`Could not capture final screenshot: ${error instanceof Error ? error.message : error}`));
      }
    }

    try {
      const summary = await summarizeResults(prompt, actions, results);
      console.log(chalk.blue(`\n📋 Final Summary:`));
      console.log(chalk.white(summary));
    } catch (error) {
      console.log(chalk.blue(`\n📋 Actions performed:`));
      actions.forEach((action, i) => {
        console.log(chalk.white(`  ${i + 1}. ${action}`));
      });
      console.log(chalk.yellow(`\n(Could not generate AI summary: ${error instanceof Error ? error.message : error})`));
    }

  } finally {
    await client.disconnect();
  }
}

export async function interactiveMode(headless: boolean = false): Promise<void> {
  checkOpenAIKey();
  
  const client = new PlaywrightMCPClient();
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const question = (prompt: string): Promise<string> => {
    return new Promise((resolve) => {
      rl.question(prompt, resolve);
    });
  };

  try {
    await client.connect(headless);
    const tools = client.getTools();

    if (tools.length === 0) {
      throw new Error('No tools available from MCP server');
    }

    console.log(chalk.green('Browser ready! Enter your commands:\n'));

    while (true) {
      const userInput = await question(chalk.cyan('> '));
      const trimmedInput = userInput.trim().toLowerCase();

      if (trimmedInput === 'exit' || trimmedInput === 'quit') {
        console.log(chalk.yellow('\nEnding session...'));
        break;
      }

      if (trimmedInput === 'help') {
        console.log(chalk.blue('\nAvailable commands:'));
        console.log(chalk.gray('- Enter any natural language command to automate the browser'));
        console.log(chalk.gray('- "screenshot" - Take a screenshot'));
        console.log(chalk.gray('- "tools" - List available MCP tools'));
        console.log(chalk.gray('- "exit" or "quit" - End the session\n'));
        continue;
      }

      if (trimmedInput === 'tools') {
        console.log(chalk.blue('\nAvailable MCP tools:'));
        console.log(chalk.gray(client.getToolsDescription()));
        console.log('');
        continue;
      }

      if (!userInput.trim()) {
        continue;
      }

      try {
        await executeSingleCommand(client, tools, userInput);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : error}`));
      }
    }
  } finally {
    rl.close();
    await client.disconnect();
  }
}

async function executeSingleCommand(
  client: PlaywrightMCPClient,
  tools: ReturnType<typeof client.getTools>,
  prompt: string
): Promise<void> {
  const actions: string[] = [];
  const results: string[] = [];
  let done = false;
  let iterations = 0;
  const maxIterations = 10;

  while (!done && iterations < maxIterations) {
    iterations++;

    const lastResult = results.length > 0 ? results[results.length - 1] : undefined;
    const response = await interpretPrompt(prompt, tools, actions, lastResult);

    console.log(chalk.gray(`  Thinking: ${response.thinking}`));

    if (response.done || response.toolCalls.length === 0) {
      done = true;
      if (response.summary) {
        console.log(chalk.green(`  ✓ ${response.summary}\n`));
      }
      break;
    }

    for (const toolCall of response.toolCalls) {
      try {
        const result = await client.callTool(toolCall.name, toolCall.arguments);
        const actionDescription = `${toolCall.name}(${JSON.stringify(toolCall.arguments)})`;
        actions.push(actionDescription);

        let resultText = 'Success';
        if (result && typeof result === 'object' && 'content' in result) {
          const content = (result as { content: Array<{ type: string; text?: string }> }).content;
          if (Array.isArray(content)) {
            const textContent = content.find(c => c.type === 'text');
            if (textContent && textContent.text) {
              resultText = textContent.text.substring(0, 300);
            }
          }
        }
        results.push(resultText);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        results.push(`Error: ${errorMsg}`);
      }
    }
  }
}
