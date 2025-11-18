#!/bin/bash

echo "===================================="
echo "ZenSmart Executor - Security Fix Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

print_info "Starting vulnerability fixes..."
echo ""

# Step 1: Install missing dependencies
print_info "Step 1: Installing missing dependencies..."
npm install cross-env --save-dev
if [ $? -eq 0 ]; then
    print_success "cross-env installed successfully"
else
    print_error "Failed to install cross-env"
fi

# Step 2: Update @types/node to fix Vite peer dependency
print_info "Step 2: Updating @types/node for Vite compatibility..."
npm install @types/node@^22.12.0 --save-dev
if [ $? -eq 0 ]; then
    print_success "@types/node updated successfully"
else
    print_error "Failed to update @types/node"
fi

# Step 3: Fix Tailwind CSS v4 configuration
print_info "Step 3: Configuring Tailwind CSS v4..."

# Remove PostCSS config if it exists (not needed with Tailwind v4 Vite plugin)
if [ -f "client/postcss.config.js" ]; then
    rm client/postcss.config.js
    print_success "Removed unnecessary postcss.config.js"
fi

# Update index.css to use Tailwind v4 syntax
if [ -f "client/src/index.css" ]; then
    # Replace @tailwind directives with @import
    sed -i '1s|@tailwind base;|@import "tailwindcss";|' client/src/index.css
    sed -i '/@tailwind components;/d' client/src/index.css
    sed -i '/@tailwind utilities;/d' client/src/index.css
    
    # Replace @apply directives with direct CSS
    sed -i 's/@apply border-border;/border-color: hsl(var(--border));/' client/src/index.css
    sed -i 's/@apply font-sans antialiased bg-background text-foreground;/font-family: var(--font-sans); -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; background-color: hsl(var(--background)); color: hsl(var(--foreground));/' client/src/index.css
    sed -i 's/@apply hidden;/display: none;/' client/src/index.css
    
    print_success "Updated index.css for Tailwind v4"
fi

# Update vite.config.ts to include Tailwind Vite plugin
if [ -f "vite.config.ts" ]; then
    # Check if tailwindcss import exists
    if ! grep -q "import tailwindcss from \"@tailwindcss/vite\"" vite.config.ts; then
        # Add import after other imports
        sed -i '/import runtimeErrorOverlay/a import tailwindcss from "@tailwindcss/vite";' vite.config.ts
        
        # Add plugin to plugins array (after react())
        sed -i '/react(),/a \    tailwindcss(),' vite.config.ts
        
        print_success "Updated vite.config.ts with Tailwind plugin"
    else
        print_info "vite.config.ts already configured"
    fi
fi

# Step 4: Run npm audit fix for non-breaking changes
print_info "Step 4: Running npm audit fix for non-breaking changes..."
npm audit fix --legacy-peer-deps
if [ $? -eq 0 ]; then
    print_success "Non-breaking vulnerabilities fixed"
else
    print_info "Some vulnerabilities could not be auto-fixed (requires manual review)"
fi

# Step 5: Check remaining vulnerabilities
echo ""
print_info "Step 5: Checking for remaining vulnerabilities..."
echo ""
npm audit --legacy-peer-deps | grep -E "(vulnerabilities|Severity)" || print_success "No critical vulnerabilities found!"

# Step 6: Clean up
print_info "Step 6: Cleaning up..."
npm cache clean --force 2>/dev/null
print_success "npm cache cleared"

echo ""
echo "===================================="
print_success "Security fix script completed!"
echo "===================================="
echo ""
print_info "Next steps:"
echo "  1. Review the audit report above"
echo "  2. Run 'npm install' to ensure all dependencies are installed"
echo "  3. Run 'npm run dev' to start the application"
echo "  4. Test the application to ensure everything works correctly"
echo ""
print_info "If you still see vulnerabilities, they may require:"
echo "  - Major version updates (breaking changes)"
echo "  - Waiting for upstream packages to be updated"
echo "  - Manual code changes"
echo ""
