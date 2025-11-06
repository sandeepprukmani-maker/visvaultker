# Windows Setup Guide

Complete setup instructions for Windows 10/11.

## Prerequisites

1. **Python 3.11+** - Download from https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   
2. **Node.js 20+** - Download from https://nodejs.org/
   - ✅ Check "Add to PATH" during installation

## Step-by-Step Installation

### 1. Open PowerShell

Press `Win + X`, select "Windows PowerShell" or "Terminal"

### 2. Install Playwright MCP Server

```powershell
npm install -g @playwright/mcp
```

**Troubleshooting:**
- If `npm` not found, restart PowerShell after installing Node.js
- If permission error, run PowerShell as Administrator

### 3. Install Python Packages

```powershell
pip install -r requirements.txt
```

**Troubleshooting:**
- If `pip` not found, try `python -m pip install -r requirements.txt`
- If SSL errors, use: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt`

### 4. Install Chromium Browser

```powershell
playwright install chromium
```

This downloads ~300MB. Ensure you have disk space and internet connection.

### 5. Set API Key

**Option A: PowerShell (Session Only)**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

**Option B: Command Prompt (Session Only)**
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

**Option C: Permanent (Recommended)**

1. Press `Win + R`
2. Type `sysdm.cpl` and press Enter
3. Click "Advanced" tab
4. Click "Environment Variables"
5. Under "User variables", click "New"
6. Variable name: `ANTHROPIC_API_KEY`
7. Variable value: `your-api-key-here`
8. Click OK, OK, OK
9. **Restart PowerShell/CMD**

## Running the Tool

### Basic Usage

```powershell
python main.py "Navigate to example.com and click the login button"
```

### View Help

```powershell
python main.py --help
```

### Example Commands

```powershell
# Use Claude (default)
python main.py "Go to github.com and search for playwright"

# Use GPT-4o
python main.py "Fill contact form" --model gpt4o

# Custom output file
python main.py "Click submit" --output my_script.py
```

## Verify Installation

Test that everything is installed correctly:

```powershell
# Check Python
python --version

# Check Node.js and npm
node --version
npm --version

# Check npx
npx --version

# Check Playwright MCP
npm list -g @playwright/mcp

# Check API key (should show your key)
echo $env:ANTHROPIC_API_KEY
```

## Common Windows Issues

### Issue: `npx` not found

**Solution:**
1. Restart PowerShell/CMD
2. Check PATH: `$env:PATH` (PowerShell) or `echo %PATH%` (CMD)
3. Verify Node.js installation: `node --version`
4. Try: `npx.cmd @playwright/mcp`

### Issue: Script execution policy error

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Permission denied

**Solution:**
- Run PowerShell as Administrator (Right-click → "Run as administrator")
- Or use user-local install: `pip install --user -r requirements.txt`

### Issue: Long path errors

**Solution (Run as Admin):**
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Then restart your computer.

### Issue: Antivirus blocking Playwright

**Solution:**
1. Add Python folder to antivirus exclusions (e.g., `C:\Users\YourName\AppData\Local\Programs\Python\`)
2. Add Node.js folder to exclusions (e.g., `C:\Program Files\nodejs\`)
3. Temporarily disable antivirus during `playwright install chromium`

### Issue: Firewall blocking connections

**Solution:**
- Allow Python through Windows Firewall
- Allow Node.js through Windows Firewall

## Output Location

Generated scripts are saved in:
```
.\generated_scripts\
```

View them:
```powershell
dir generated_scripts
```

Run a generated script:
```powershell
python generated_scripts\automation_*.py
```

## Tips for Windows Users

1. **Use PowerShell** - It's more powerful than CMD
2. **Run as Administrator** - If you encounter permission issues
3. **Check PATH** - Ensure Python and Node.js are in your PATH
4. **Antivirus** - May slow down or block installations
5. **Disk Space** - Need ~1GB free for all dependencies

## Getting API Keys

### Claude (Anthropic)
1. Visit https://console.anthropic.com/
2. Sign up / Login
3. Go to "API Keys"
4. Create new key
5. Copy and save securely

### GPT-4o (OpenAI)
1. Visit https://platform.openai.com/
2. Sign up / Login
3. Go to "API Keys"
4. Create new secret key
5. Copy and save securely

### Gemini (Google)
1. Visit https://aistudio.google.com/
2. Sign up / Login
3. Click "Get API Key"
4. Create new API key
5. Copy and save securely

## Quick Test

After setup, test with a simple command:

```powershell
python main.py "Go to example.com"
```

This should:
1. ✅ Start the MCP server
2. ✅ Open Chromium browser
3. ✅ Navigate to example.com
4. ✅ Generate a Python script
5. ✅ Save to `generated_scripts\`

## Support

If issues persist:
1. Check all prerequisites are installed
2. Restart PowerShell/CMD
3. Verify API key is set correctly
4. Try running as Administrator
5. Check antivirus/firewall settings

For more help, see the main [SETUP.md](SETUP.md) file.
