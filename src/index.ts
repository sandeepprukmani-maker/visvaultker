#!/usr/bin/env node
import 'dotenv/config';
import { program } from 'commander';
import chalk from 'chalk';
import { automateWithPrompt, interactiveMode } from './automation.js';

program
  .name('playwright-mcp-cli')
  .description('CLI tool for browser automation using Playwright MCP with natural language prompts')
  .version('1.0.0');

program
  .command('run')
  .description('Execute a browser automation task from a natural language prompt')
  .argument('<prompt>', 'Natural language description of the automation task')
  .option('--headless', 'Run browser in headless mode', false)
  .option('--screenshot <path>', 'Save screenshot to the specified path')
  .action(async (prompt: string, options: { headless: boolean; screenshot?: string }) => {
    console.log(chalk.blue('\n🚀 Starting browser automation...\n'));
    console.log(chalk.gray(`Prompt: "${prompt}"\n`));
    
    try {
      await automateWithPrompt(prompt, {
        headless: options.headless,
        screenshotPath: options.screenshot,
      });
    } catch (error) {
      console.error(chalk.red('\n❌ Automation failed:'), error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

program
  .command('interactive')
  .alias('i')
  .description('Start interactive mode for browser automation')
  .option('--headless', 'Run browser in headless mode', false)
  .action(async (options: { headless: boolean }) => {
    console.log(chalk.blue('\n🎭 Starting Playwright MCP Interactive Mode\n'));
    console.log(chalk.gray('Type your automation commands in natural language.'));
    console.log(chalk.gray('Type "exit" or "quit" to end the session.\n'));
    
    try {
      await interactiveMode(options.headless);
    } catch (error) {
      console.error(chalk.red('\n❌ Interactive mode failed:'), error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

program.parse();
