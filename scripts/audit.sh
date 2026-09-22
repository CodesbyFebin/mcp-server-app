#!/bin/bash
# MCPServer OS — Forensic Audit Script
# Phase 0: Repository Forensics
# This script helps gather basic information about the repository state
# for the forensic audit phase.

set -euo pipefail

echo "=== MCPServer OS Forensic Audit ==="
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# 1. Repository Identity
echo "1. Repository Identity"
echo "----------------------"
echo "Repository URL: $(git remote get-url origin 2>/dev/null || echo "Not a git repository or no origin remote")"
echo "Current Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "Not a git repository")"
echo "HEAD SHA: $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")"
echo "Dirty State: $(if git diff-index --quiet HEAD 2>/dev/null; then echo "Clean"; else echo "Dirty"; fi)"
echo ""

# 2. Stack Information
echo "2. Stack Information"
echo "--------------------"
echo "Node.js Version: $(node --version 2>/dev/null || echo "Not installed")"
echo "npm Version: $(npm --version 2>/dev/null || echo "Not installed")"
echo "pnpm Version: $(pnpm --version 2>/dev/null || echo "Not installed")"
echo "yarn Version: $(yarn --version 2>/dev/null || echo "Not installed")"
echo "Python Version: $(python --version 2>/dev/null || python3 --version 2>/dev/null || echo "Not installed")"
echo "PostgreSQL Version: $(psql --version 2>/dev/null || echo "Not installed or not in PATH")"
echo "Redis Version: $(redis-server --version 2>/dev/null || echo "Not installed or not in PATH")"
echo "Docker Version: $(docker --version 2>/dev/null || echo "Not installed")"
echo "Docker Compose Version: $(docker-compose --version 2>/dev/null || docker compose --version 2>/dev/null || echo "Not installed")"
echo ""

# 3. File Structure Overview
echo "3. File Structure Overview (Top-level Directories)"
echo "--------------------------------------------------"
find . -maxdepth 1 -type d -not -path "*/\.*" -not -path "./node_modules*" -not -path "./temp-clone*" -not -path "./mcp-servers-master*" | sort | while read dir; do
  echo "- $(basename "$dir")"
done
echo ""

# 4. Key Files Check
echo "4. Key Files Check"
echo "------------------"
files_to_check=(
  "package.json"
  "pnpm-lock.yaml"
  "requirements.txt"
  "tsconfig.json"
  "next.config.mjs"
  "vercel.json"
  "vitest.config.mjs"
  "tailwind.config.ts"
  "postcss.config.cjs"
  ".env.example"
  ".gitignore"
  "README.md"
  "ARCHITECTURE.md"
  "PROJECT-TRACKER.md"
  "pii-redact-middleware.ts"
  "upi-sandbox-integration.py"
  "app-mcpserver-in/package.json"
  "app-mcpserver-in/services/api/lib/middleware/pii-redact.ts"
  "app-mcpserver-in/services/mcp-server/main.py"
  "app-mcpserver-in/deploy/docker/docker-compose.yml"
  "app-mcpserver-in/services/mcp-server/package.json"
  "app-mcpserver-in/services/gateway/package.json"
  "app-mcpserver-in/services/workflow-engine/package.json"
  "app-mcpserver-in/services/registry-sync/package.json"
  "app-mcpserver-in/packages/contracts/package.json"
  "app-mcpserver-in/packages/database/package.json"
  "app-mcpserver-in/packages/evidence/package.json"
  "app-mcpserver-in/packages/policy/package.json"
  "app-mcpserver-in/packages/security/package.json"
  "app-mcpserver-in/packages/ui/package.json"
)

for file in "${files_to_check[@]}"; do
  if [ -f "$file" ]; then
    echo "✓ $file"
  else
    echo "✗ $file (MISSING)"
  fi
done
echo ""

# 5. Directory Structure Details
echo "5. Key Directory Structures"
echo "---------------------------"
dirs_to_check=(
  "app-mcpserver-in/apps"
  "app-mcpserver-in/services"
  "app-mcpserver-in/packages"
  "app-mcpserver-in/deploy"
  "app-mcpserver-in/scripts"
  "app-mcpserver-in/tests"
)

for dir in "${dirs_to_check[@]}"; do
  if [ -d "$dir" ]; then
    count=$(find "$dir" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo "✓ $dir ($count subdirectories)"
  else
    echo "✗ $dir (MISSING)"
  fi
done
echo ""

# 6. Next.js Specific Checks
echo "6. Next.js Specific Checks"
echo "--------------------------"
if [ -f "package.json" ]; then
  echo "Next.js Version: $(grep -o '"next": *"[^"]*"' package.json | cut -d'"' -f4 || echo "Not specified")"
  echo "React Version: $(grep -o '"react": *"[^"]*"' package.json | cut -d'"' -f4 || echo "Not specified")"
  echo "TypeScript Version: $(grep -o '"typescript": *"[^"]*"' package.json | cut -d'"' -f4 || echo "Not specified")"
fi
echo ""

# 7. Basic Metrics
echo "7. Basic Repository Metrics"
echo "---------------------------"
if [ -d ".git" ]; then
  echo "Total Commits: $(git rev-list --count HEAD 2>/dev/null || echo "Unable to count")"
  echo "Contributors: $(git shortlog -s -n --all 2>/dev/null | wc -l || echo "Unable to count")"
  echo "Branches: $(git branch -r | grep -v HEAD | wc -l || echo "Unable to count")"
  echo "Tags: $(git tag | wc -l || echo "Unable to count")"
else
  echo "Not a git repository - skipping git metrics"
fi

# File counts (excluding node_modules and hidden files)
echo "TypeScript Files: $(find . -name "*.ts" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo "TSX Files: $(find . -name "*.tsx" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo "JavaScript Files: $(find . -name "*.js" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo "JSX Files: $(find . -name "*.jsx" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo "Python Files: $(find . -name "*.py" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo "Markdown Files: $(find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/\.*" 2>/dev/null | wc -l || echo "0")"
echo ""

echo "=== Audit Complete ==="
echo "Save this output to reports/00-BASELINE.md for further analysis"
echo ""