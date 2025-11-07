#!/usr/bin/env python3
import asyncio
import argparse
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from config import MODEL_CONFIGS, ModelType, MCP_SERVER_COMMAND, MCP_SERVER_ARGS, OUTPUT_DIR, TRACE_DIR
from mcp_client import PlaywrightMCPClient
from agents import ExecutorAgent, CodeGeneratorAgent, HealerAgent

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert natural language to rerunnable Python Playwright scripts using MCP"
    )
    
    parser.add_argument(
        "task",
        help="Natural language description of the automation task"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        choices=["claude", "gpt4o", "gemini"],
        default="claude",
        help="AI model to use (default: claude)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for generated script (default: auto-generated)"
    )
    
    parser.add_argument(
        "--no-heal",
        action="store_true",
        help="Disable auto-healing if generated script fails"
    )
    
    return parser.parse_args()


async def main():
    args = parse_args()
    
    console.print(Panel.fit(
        "[bold cyan]Playwright MCP Automation Script Generator[/bold cyan]\n"
        f"Model: {MODEL_CONFIGS[args.model]['display_name']}",
        border_style="cyan"
    ))
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TRACE_DIR, exist_ok=True)
    
    model = args.model
    task_description = args.task
    
    try:
        async with PlaywrightMCPClient(MCP_SERVER_COMMAND, MCP_SERVER_ARGS) as mcp_client:
            executor = ExecutorAgent(model, mcp_client)
            result = await executor.execute_task(task_description)
            
            if not result["success"]:
                console.print("[bold red]✗ Task execution failed[/bold red]")
                return 1
            
            console.print("\n[bold green]✓ Task execution successful![/bold green]")
            
            generator = CodeGeneratorAgent(model)
            generated_code = await generator.generate_code(result["trace"], task_description)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if args.output:
                output_file = args.output
            else:
                safe_task_name = "".join(c if c.isalnum() else "_" for c in task_description[:30])
                output_file = os.path.join(OUTPUT_DIR, f"automation_{safe_task_name}_{timestamp}.py")
            
            with open(output_file, "w") as f:
                f.write(generated_code)
            
            console.print(f"\n[bold blue]📄 Generated script saved to: {output_file}[/bold blue]\n")
            
            syntax = Syntax(generated_code, "python", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Generated Code", border_style="blue"))
            
            if not args.no_heal:
                console.print("\n[yellow]Testing generated script...[/yellow]")
                
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, output_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    error_message = stderr.decode() if stderr else "Unknown error"
                    console.print(f"[bold red]✗ Generated script failed with error:[/bold red]\n{error_message}")
                    
                    healer = HealerAgent(model)
                    console.print("\n[yellow]Attempting to auto-heal the script...[/yellow]")
                    
                    healed_code = await healer.heal_code(generated_code, error_message)
                    
                    healed_output = output_file.replace(".py", "_healed.py")
                    with open(healed_output, "w") as f:
                        f.write(healed_code)
                    
                    console.print(f"\n[bold green]✓ Healed script saved to: {healed_output}[/bold green]\n")
                    
                    syntax = Syntax(healed_code, "python", theme="monokai", line_numbers=True)
                    console.print(Panel(syntax, title="Healed Code", border_style="green"))
                else:
                    console.print("[bold green]✓ Generated script executed successfully![/bold green]")
            
            console.print(f"\n[bold cyan]Summary:[/bold cyan]")
            console.print(f"  Task: {task_description}")
            console.print(f"  Model: {MODEL_CONFIGS[model]['display_name']}")
            console.print(f"  Output: {output_file}")
            console.print(f"  Trace items: {len(result['trace'])}")
            
            return 0
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
