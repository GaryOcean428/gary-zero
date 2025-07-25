# Development Standards & Practices

## Coding Conventions
- **Language:** TypeScript, Python
- **Framework:** React (functional components, hooks)
- **Node Version:** 22.x (latest LTS)
- **Package Manager:** Yarn 4.9.1 (preferred), pnpm (secondary), npm (fallback)
- **Linter:** ESLint for JavaScript, Ruff for Python
- **Formatter:** Prettier for JavaScript, Black for Python
- **Indentation:** 2 spaces
- **Max Line Length:** 100 characters

### Language Specific
- **JavaScript/TypeScript:**
  - Use `const` over `let`, avoid `var`
  - Follow camelCase for variables/functions, PascalCase for classes/interfaces
  - Enable strict typing in TypeScript

- **Python:**
  - Adhere to PEP-8 guidelines
  - Use type hints extensively

## Version Minimums
- **Next.js:** 15.1.6+
- **React:** 19.0.0+
- **Node.js:** 22.x
- **TypeScript:** 5.5+
- **Vite:** 4.4.7+
- **Python Dependencies:** Refer to `pyproject.toml` for specific packages

## Duplication Prevention
- **Check Existing Implementations:** Always search for existing similar functionality
- **Reuse and Extend:** Prefer extension/composition over duplication
- **Shared Logic:** Place common utilities in `/shared` directory

## Structured-Thinking Tags
- Use `[thinking]` tags for planning and decision-making
- Prefer concise step-reduction: `Problem → Solution → Implementation Flow`

## Testing Strategy
- **Test Framework:** Vitest and Pytest
- **Coverage Requirement:** Minimum 80%
- **Types:** Unit tests, integration tests, and E2E tests
- **Automated Testing:** Via CI pipeline with scheduled runs
- **Mocking:** Use exclusively for tests

## Pull Request Checklist
1. Dynamic security scan (Bandit, Safety)
2. Ensure all tests pass with minimum coverage
3. Linting and formatting checks
4. Review code quality and adherence to standards
5. Validate against current documentation

## Code Quality  26 Standards Rules Integration
- Ensure the alignment of multi-agent systems with Gary8D standards
- Validate AI Model compliance and ensure updated models
- Apply Security Specialist review for critical sections

## BuilderMethods Alignment
- Follow `Build vs. Remove` philosophy
- Ensure complete documentation review and feature specification before implementation
