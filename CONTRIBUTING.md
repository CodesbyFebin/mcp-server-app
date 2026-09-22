# Contributing to MCPServer OS

Thank you for considering contributing to MCPServer OS! This document outlines our development workflow, coding standards, and pull request process.

## Development Philosophy

MCPServer OS follows an **Evidence-First** approach:
- Focus on verifiable technical controls rather than compliance claims
- Immutable deployment revisions with hash-chained evidence trails
- Zero-trust architecture with tenant isolation and least-privilege access
- Observable interactions from client request to tool execution and response

## Getting Started

### Prerequisites
- Node.js 18+ (or version specified in `.nvmrc`)
- Python 3.9+
- Docker & Docker Compose
- Git
- PostgreSQL 15+
- Redis 7+

### Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/Indian-MCP-Server.git
cd Indian-MCP-Server

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (optional but recommended)
npm run prepare

# Copy environment example
cp .env.example .env
# Edit .env with your development configuration

# Initialize database
npx prisma migrate dev

# Start development server
npm run dev
```

## Project Structure

```
apps/
  web                  # Next.js App Router (app.mcpserver.in)
  cli                  # MCP Server CLI (mcpserver)
  docs                 # Documentation

services/
  control-plane        # Orgs, Workspaces, Deployments
  gateway              # MCP Transport, JSON-RPC, Auth
  worker               # Background jobs, healing
  registry             # mcpserver.in trust bridge

packages/
  contracts            # Zod schemas, API contracts, API contracts
  database             # Prisma, migration scripts
  evidence             # Hash chain, ledger logic
  policy               # Policy engine, rules
  security             # Secrets, isolation, SSRF
  ui                   # Shared React components

scripts/
  audit.sh             # Forensic scripts
  deploy.sh            # Deployment scripts
```

## Making Changes

### Branch Naming
Use descriptive branch names:
- `feat/feature-name` for new features
- `fix/bug-description` for bug fixes
- `docs/documentation-update` for documentation
- `refactor/code-improvement` for refactoring
- `test/test-addition` for test-related changes

### Commit Messages
Follow conventional commits format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Build process or auxiliary tool changes

Examples:
- `feat(EVD-001): implement tenant-scoped evidence ledger`
- `fix(MCP-003): enforce tool policy before execution`
- `test(CORE-002): prove cross-tenant organization isolation`
- `docs: update deployment guide with new env vars`

### Coding Standards

#### TypeScript/JavaScript
- Use TypeScript strict mode
- Follow ESLint and Prettier configurations
- Prefer functional programming patterns
- Avoid `any` type when possible
- Use meaningful variable and function names

#### Python
- Follow PEP 8 style guidelines
- Use type hints where beneficial
- Write clear docstrings for public functions
- Handle exceptions appropriately

#### Database Changes
- Use Prisma migrations for schema changes
- Never modify production data directly
- Test migrations on copy of production data
- Include both up and down migrations when possible

#### Security Considerations
- Never commit secrets or API keys
- Validate all inputs (server-side)
- Implement proper authentication and authorization
- Use parameterized queries to prevent SQL injection
- Sanitize outputs to prevent XSS

## Pull Request Process

### Before Submitting
1. Ensure your code passes linting and typechecking:
   ```bash
   npm run lint
   npm run typecheck
   ```
2. Run the test suite:
   ```bash
   npm test
   ```
3. Ensure your changes are properly documented
4. Squash commits if necessary for clean history
5. Update PROJECT-TRACKER.md if your work affects tracked features

### Submitting a PR
1. Push your branch to your fork
2. Open a pull request against the `kilo/orbital-eagle-zbx` branch
3. Fill out the PR template completely
4. Link to any related issues
5. Request review from maintainers

### PR Requirements
- [ ] Description clearly explains the problem and solution
- [ ] Related issues are referenced
- [ ] Code follows project conventions
- [ ] Tests pass and new tests are added where appropriate
- [ ] Documentation is updated if needed
- [ ] No console.log statements or debugging code
- [ ] No hardcoded secrets or credentials
- [ ] Proper error handling implemented
- [ ] Performance considerations addressed

## Testing

### Test Types
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test full user workflows
- **Security Tests**: Test for vulnerabilities and edge cases
- **Performance Tests**: Test under load and stress conditions

### Running Tests
```bash
# Run all tests
npm test

# Run only unit tests
npm run test:unit

# Run only integration tests
npm run test:integration

# Run tests with coverage
npm run test:coverage
```

### Test File Conventions
- Unit tests: `*.test.ts` or `*.test.tsx` alongside source
- Integration tests: `__tests__/` directory
- E2E tests: `cypress/` or `playground/` directory
- Test files should mirror the source file structure

## Documentation

### Documentation Standards
- Write clear, concise documentation
- Include code examples where helpful
- Keep documentation close to the code it describes
- Update documentation when changing functionality
- Use markdown formatting consistently

### Where to Document
- **README.md**: High-level overview and getting started
- **ARCHITECTURE.md**: System design and architecture decisions
- **PROJECT-TRACKER.md**: Implementation progress and roadmap
- **Inline Comments**: Complex logic and non-obvious implementations
- **API Documentation**: JSDoc/Typedoc for public interfaces
- **Deployment Guides**: Environment-specific setup instructions

## Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (Node version, OS, etc.)
- Relevant logs or error messages
- Steps to mitigate or workaround (if known)

Label issues appropriately:
- `bug`: Something is broken
- `enhancement`: New feature or improvement
- `documentation`: Documentation needs improvement
- `question`: Question about usage or implementation
- `security`: Security vulnerability (please email security@mcpserver.in for critical issues)

## Community

- Be respectful and welcoming to all contributors
- Follow the [Contributor Covenant](https://www.contributor-covenant.org/)
- Help others when you can
- Credit contributors appropriately
- Celebrate successes together

## License

By contributing to MCPServer OS, you agree that your contributions will be licensed under the Apache 2.0 License.

Thank you for helping make MCPServer OS better!