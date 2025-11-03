# Contributing Guide

Thank you for contributing to the Child Growth Assistant project!

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-new-safety-check`
- `fix/refusal-template-bug`
- `docs/update-deployment-guide`

### 2. Make Changes

- Write clear, readable code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests Locally

**Backend**:
```bash
cd backend
pytest tests/ -v
```

**Frontend**:
```bash
cd frontend
npm run lint
npx playwright test e2e/assistant.spec.ts
```

### 4. Commit Changes

Use conventional commit messages:
- `feat: add new safety check`
- `fix: resolve refusal template bug`
- `docs: update deployment guide`
- `test: add E2E test for crisis detection`
- `refactor: simplify guardrails logic`

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- Clear title and description
- Reference to related issue/task
- Screenshots (if UI changes)

### 6. Code Review

- All PRs require at least one approval
- CI must pass (lint, tests, build)
- Address reviewer feedback

### 7. Merge

Once approved and CI is green:
- Squash and merge (preferred)
- Delete branch after merge

---

## Code Style

### Python (Backend)

- Use `black` for formatting
- Follow PEP 8 style guide
- Maximum line length: 120 characters
- Type hints where possible

```bash
# Format code
black app/ tests/

# Check style
flake8 app/
```

### TypeScript (Frontend)

- Use ESLint configuration
- Follow Next.js conventions
- TypeScript strict mode enabled

```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit
```

---

## Testing Guidelines

### Unit Tests

- Write tests for all new functions
- Aim for >80% code coverage
- Use descriptive test names

**Example**:
```python
def test_medical_adhd_diagnosis(guard):
    """Should refuse medical diagnosis questions."""
    category, template = guard.classify_request("Does my child have ADHD?")
    assert category == 'medical'
    assert template is not None
```

### E2E Tests

- Test complete user flows
- Use descriptive test IDs
- Keep tests independent

**Example**:
```typescript
test('Medical refusal - ADHD question', async ({ page }) => {
  // Test steps
});
```

---

## OpenSpec Workflow

For major features, use OpenSpec:

1. **Create Proposal**:
   ```bash
   openspec propose add-feature-name
   ```

2. **Fill out proposal**: Describe why, what changes, impact

3. **Create Tasks**: Break down into checklist items

4. **Implement**: Work through tasks

5. **Archive**: After completion
   ```bash
   openspec archive add-feature-name
   ```

---

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No console.log/print statements (use proper logging)
- [ ] Environment variables documented
- [ ] Breaking changes documented

---

## Commit Message Format

Use conventional commits:

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples**:
```
feat: add HITL queue for crisis cases

Implements human-in-the-loop queue for crisis detection.
Routes crisis prompts to mentor queue with <500ms latency.

Closes #123
```

```
fix: resolve 'beat' keyword missing in crisis detection

Added 'beat', 'hit', 'slap' to crisis keywords after red-team testing.
```

---

## Questions?

- Check documentation in `docs/`
- Review OpenSpec proposals in `openspec/changes/`
- Ask in team chat or create discussion

---

*Thank you for contributing!* 🎉

