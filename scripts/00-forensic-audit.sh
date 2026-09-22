#!/bin/bash
# MCPServer OS — Phase 0 Forensic Audit Script
set -e

echo "🔍 Starting MCPServer OS Forensic Audit..."
echo "==========================================="

# 1. Repository Identity
echo "📦 Checking Repository Identity..."
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "Unknown")
BRANCH=$(git branch --show-current)
HEAD_SHA=$(git rev-parse HEAD)
DIRTY=$(git status --porcelain | wc -l)

echo "   Remote: $REPO_URL"
echo "   Branch: $BRANCH"
echo "   HEAD: $HEAD_SHA"
echo "   Dirty State: $DIRTY"

# 2. Stack Verification
echo "🛠️ Checking Stack..."
NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
PKG_MANAGER="npm"

if command -v pnpm &> /dev/null; then
  PKG_MANAGER="pnpm"
  PNPM_VERSION=$(pnpm -v)
  echo "   Package Manager: pnpm ($PNPM_VERSION)"
else
  echo "   Package Manager: npm ($NPM_VERSION)"
fi
echo "   Node Version: $NODE_VERSION"

# 3. Structure Analysis
echo "📂 Analyzing Structure..."
if [ -d "apps" ]; then
  echo "   ✅ Structure: apps/ exists (Normalized)"
else
  echo "   ⚠️  Structure: apps/ missing (Monolithic)"
fi

if [ -d "services" ]; then
  echo "   ✅ Structure: services/ exists"
else
  echo "   ⚠️  Structure: services/ missing"
fi

if [ -d "packages" ]; then
  echo "   ✅ Structure: packages/ exists"
else
  echo "   ⚠️  Structure: packages/ missing"
fi

# 4. Component Check
echo "🧩 Checking Core Components..."
COMPONENTS=(
  "app-mcpserver-in/:Control Plane"
  "pii-redact-middleware.ts:DPDP Middleware"
  "upi-sandbox-integration.py:UPI Integration"
  "prisma/:Database Schema"
  "Dockerfile:Docker Config"
  ".github/workflows/:CI/CD"
)

for item in "${COMPONENTS[@]}"; do
  path="${item%:*}"
  name="${item#*:}"
  if [ -e "$path" ]; then
    echo "   ✅ $name"
  else
    echo "   ❌ $name"
  fi
done

# 5. Generate Reports Directory
mkdir -p reports

# 6. Create Baseline Report
echo "📝 Generating reports/00-BASELINE.md..."
cat > reports/00-BASELINE.md << REPORT_EOF
# 📊 MCPServer OS — Repository Baseline Report
**Generated:** $(date -u +"%Y-%m-%d")
**Repository:** $REPO_URL
**Branch:** $BRANCH
**Head Commit:** $HEAD_SHA

## 1. Repository Identity
| Attribute | Value |
|-----------|-------|
| Remote URL | $REPO_URL |
| Active Branch | $BRANCH |
| Head Commit | $HEAD_SHA |
| Dirty State | $DIRTY |

## 2. Stack
| Attribute | Value |
|-----------|-------|
| Node Version | $NODE_VERSION |
| Package Manager | $PKG_MANAGER |

## 3. Structure Status
- **apps/**: $([ -d "apps" ] && echo "Present" || echo "Missing")
- **services/**: $([ -d "services" ] && echo "Present" || echo "Missing")
- **packages/**: $([ -d "packages" ] && echo "Present" || echo "Missing")

## 4. Core Components
$(for item in "${COMPONENTS[@]}"; do
  path="${item%:*}"
  name="${item#*:}"
  if [ -e "$path" ]; then
    echo "- ✅ $name"
  else
    echo "- ❌ $name"
  fi
done)

## 5. Next Steps
1. Normalize structure to \`apps/\`, \`services/\`, \`packages/\`.
2. Initialize \`PROJECT-TRACKER.md\`.
3. Begin Phase 1: Repository Normalization.
REPORT_EOF

echo "✅ Baseline report generated: reports/00-BASELINE.md"

# 7. Create Gap Matrix
echo "📊 Generating reports/00-GAP-MATRIX.csv..."
cat > reports/00-GAP-MATRIX.csv << CSV_EOF
Component,Current Status,Required Status,Gap,Priority
Repository Structure,Monolithic,apps/services/packages,High,P0
Database Schema,Unknown,PostgreSQL+RLS,High,P0
Evidence Ledger,Missing,Tamper-evident chain,High,P0
Gateway Plane,Unknown,MCP Transport+Policy,High,P0
Secret Vault,Unknown,Provider-neutral interface,High,P0
CI/CD,Pending,GitHub Actions+Lint/Test,Medium,P1
Documentation,Partial,README+ARCHITECTURE,Medium,P1
CSV_EOF

echo "✅ Gap matrix generated: reports/00-GAP-MATRIX.csv"

echo "==========================================="
echo "🎉 Forensic Audit Complete!"
echo "📂 Reports saved to: reports/"
