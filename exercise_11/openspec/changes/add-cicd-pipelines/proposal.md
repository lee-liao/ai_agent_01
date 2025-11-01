# Add CI/CD Pipelines

## Why
Automated testing and deployment ensure code quality, catch bugs early, and enable fast, reliable releases. CI blocks bad code from merging; CD automatically deploys passing builds to staging.

## What Changes
- Create `.github/workflows/ci.yml` for lint, type-check, unit tests, e2e tests, and build
- Create `.github/workflows/cd.yml` for staging deployment
- Red CI blocks merge; green tag auto-deploys to staging
- Add status badges to README

## Impact
- Affected specs: New capability `cicd-automation`
- Affected code:
  - `.github/workflows/ci.yml` - Continuous integration
  - `.github/workflows/cd.yml` - Continuous deployment
  - `README.md` - Status badges
  - `.github/dependabot.yml` - Dependency updates

