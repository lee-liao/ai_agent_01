# GitHub Branch Protection Rules Setup Guide

This guide walks you through configuring branch protection rules for the `main` branch to ensure code quality and prevent broken code from being merged.

## Overview

Branch protection rules enforce:
- ✅ All CI checks must pass before merging
- ✅ Code reviews are required
- ✅ Automatic branch deletion after merge
- ✅ Protection against force pushes and branch deletion

## Prerequisites

- Admin access to the GitHub repository
- CI workflows already configured (`.github/workflows/exercise_11_ci.yml`)

## ⚠️ Important: Checks Must Run First!

**If you see "No required checks" or "No checks have been added" in the status checks section**, this is normal! GitHub only shows status checks that have **already run at least once** on your repository.

**Before configuring branch protection**, you need to:

1. **Trigger the CI workflow** by creating a test PR or pushing to a branch
2. **Wait for the workflow to complete** (takes ~5-10 minutes)
3. **Return to branch protection settings** - the checks will now appear

See the **"Getting Checks to Appear"** section below for detailed steps.

## Step-by-Step Instructions

### Step 1: Navigate to Branch Settings

1. Go to your GitHub repository
2. Click **Settings** (top menu bar)
3. In the left sidebar, click **Branches** (under "Code and automation")

### Step 2: Add Branch Protection Rule

1. Scroll to the **Branch protection rules** section
2. Click **Add rule** or **Add branch protection rule** button

### Step 3: Configure Branch Name Pattern

1. In the **Branch name pattern** field, enter: `main`
   - This will protect the `main` branch
   - You can also add `develop` if you want to protect that branch too

### Step 4: Require Pull Request Before Merging

1. **Check the box "Require a pull request before merging"**
   - This is the FIRST thing you should enable - it unlocks the review options below
   - After checking this, you'll see additional options appear

2. **Configure pull request requirements** (these appear after checking step 1):
   - Check **"Require pull request reviews before merging"**
   - Set **Required number of approvals**: `1` (or more if your team prefers)
   - (Optional) Check **"Dismiss stale pull request approvals when new commits are pushed"**
     - This ensures reviewers re-review if code changes after approval
   - (Optional) Check **"Require review from Code Owners"** if you have a CODEOWNERS file

### Step 5: Enable Required Status Checks

> **⚠️ If you see "No required checks" or "No checks have been added":**
> 
> **STOP HERE** and go to the **"Getting Checks to Appear"** section below. You must trigger the CI workflow first before checks will appear in this dropdown.

1. Check the box **"Require status checks to pass before merging"**
2. Check **"Require branches to be up to date before merging"**
   - This ensures PRs are rebased/updated with the latest `main` branch

3. In the **"Status checks that are required"** section, you'll see a search box with placeholder "Search for status checks in the last week for this repository".
   **IMPORTANT**: You must **type the job names** in the search box - they won't auto-populate!
   
   Type each of the following job names one by one and select them:
   - Type `lint-backend` and select it
   - Type `type-check-backend` and select it
   - Type `test-backend` and select it
   - Type `lint-frontend` and select it
   - Type `test-e2e` and select it
   - Type `build` and select it

   **Note**: The search box uses exact matching - type the exact job name as shown above. After typing, the check should appear and you can click to select it.

   **If checks don't appear when typing**: See the "Getting Checks to Appear" section below.

### Step 6: Additional Protection (Recommended)

1. Check **"Require conversation resolution before merging"**
   - Ensures all PR comments/threads are resolved before merging
   - This is highly recommended for code quality

2. **Do NOT** check **"Require signed commits"** (optional, usually not needed unless your organization requires it)

3. **Do NOT** check **"Require linear history"** (optional, prevents merge commits - usually not necessary)

4. **Do NOT** check **"Require deployments to succeed before merging"** (unless you have deployment environments set up)

5. **Do NOT** check **"Lock branch"** (makes branch read-only - too restrictive)

6. **Check "Do not allow bypassing the above settings"** (recommended for security)
   - This ensures even administrators must follow the rules
   - Prevents accidental bypasses

### Step 7: Enable Branch Deletion

Scroll down to the **"Rules applied to everyone including administrators"** section:

1. **Do NOT** check **"Allow force pushes"** (leave unchecked for security)
   - Prevents rewriting history on protected branch

2. **Check "Allow deletions"**
   - This allows users with push access to delete branches (including the protected branch itself)
   - **Note**: This does NOT automatically delete branches after PR merge
   - This only allows manual deletion if needed

**Automatic Branch Deletion After PR Merge:**
- GitHub automatically deletes the source branch when you merge a PR **if you check the "Delete branch" option during merge**
- This is a **per-PR checkbox** that appears when you merge a pull request
- The checkbox is usually **checked by default** for most users
- There is **no global repository setting** to enable automatic deletion for all PRs
- The deletion happens via the checkbox on each PR's merge button

**To delete a branch after PR merge:**
1. When merging a PR, look for the checkbox "Delete [branch-name]" near the merge button
2. Make sure it's checked (it usually is by default)
3. After merging, the branch will be automatically deleted

**Note**: The "Allow deletions" option in branch protection only allows manual deletion permissions - it doesn't control automatic deletion after PR merge.

### Step 8: Save the Rule

1. Click **Create** or **Save changes** button at the bottom
2. You should see a confirmation message

## Getting Checks to Appear

If you see **"No required checks"** or **"No checks have been added"** when configuring branch protection, follow these steps:

### Option 1: Trigger CI via Test PR (Recommended)

1. **Create a test branch:**
   ```bash
   git checkout -b test-ci-trigger
   ```

2. **Make a small change** (e.g., add a comment to any file in `exercise_11/`):
   ```bash
   # Add a comment to README or any file
   echo "# Test CI trigger" >> exercise_11/README.md
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "test: trigger CI workflow"
   git push origin test-ci-trigger
   ```

4. **Create a Pull Request:**
   - Go to GitHub → Pull Requests → New Pull Request
   - Select `test-ci-trigger` → `main`
   - Create the PR (you don't need to merge it)

5. **Wait for CI to complete:**
   - Go to the PR page
   - Click on the "Checks" tab or view the Actions tab
   - Wait for all jobs to complete (~5-10 minutes)
   - You should see: `lint-backend`, `type-check-backend`, `test-backend`, `lint-frontend`, `test-e2e`, `build`

6. **Return to Branch Protection Settings:**
   - Go back to Settings → Branches → Branch protection rules
   - Edit your `main` branch rule
   - Scroll to "Status checks that are required"
   - **Click in the search box and type each job name** (they won't auto-populate!):
     - Type `lint-backend` and select it
     - Type `type-check-backend` and select it
     - Type `test-backend` and select it
     - Type `lint-frontend` and select it
     - Type `test-e2e` and select it
     - Type `build` and select it

### Option 2: Push Directly to Main (If you have access)

1. **Make a small change and push:**
   ```bash
   git checkout main
   echo "# CI test" >> exercise_11/.gitignore
   git add exercise_11/.gitignore
   git commit -m "chore: trigger CI for branch protection setup"
   git push origin main
   ```

2. **Wait for CI to complete:**
   - Go to Actions tab in GitHub
   - Find the "Exercise 11 CI" workflow run
   - Wait for it to complete

3. **Return to branch protection settings:**
   - Go to Settings → Branches → Branch protection rules
   - Edit your `main` branch rule
   - Scroll to "Status checks that are required"
   - **Click in the search box and type each job name** (they won't auto-populate!):
     - Type `lint-backend` and select it
     - Type `type-check-backend` and select it
     - Type `test-backend` and select it
     - Type `lint-frontend` and select it
     - Type `test-e2e` and select it
     - Type `build` and select it

### Option 3: Manual Workflow Trigger (If Available)

1. Go to **Actions** tab in GitHub
2. Select **"Exercise 11 CI"** workflow
3. Click **"Run workflow"** button (if available)
4. Select branch: `main` or any feature branch
5. Click **"Run workflow"**
6. Wait for completion (~5-10 minutes)
7. Return to branch protection settings:
   - Go to Settings → Branches → Branch protection rules
   - Edit your `main` branch rule
   - Scroll to "Status checks that are required"
   - **Click in the search box and type each job name** (they won't auto-populate!):
     - Type `lint-backend` and select it
     - Type `type-check-backend` and select it
     - Type `test-backend` and select it
     - Type `lint-frontend` and select it
     - Type `test-e2e` and select it
     - Type `build` and select it

### Verify Checks Are Available

After triggering CI, verify checks appear:

1. Go to **Settings** → **Branches**
2. Click **Edit** on your branch protection rule
3. Scroll to **"Require status checks to pass before merging"**
4. Click in the **"Search for status checks"** field
5. **Type each job name** in the search box - they won't auto-populate! Type:
   - `lint-backend` (should appear after typing)
   - `type-check-backend` (should appear after typing)
   - `test-backend` (should appear after typing)
   - `lint-frontend` (should appear after typing)
   - `test-e2e` (should appear after typing)
   - `build` (should appear after typing)
6. Select each check as it appears

If checks still don't appear after 10-15 minutes:
- Check that `.github/workflows/exercise_11_ci.yml` exists and is valid
- Verify the workflow ran successfully in the Actions tab
- Check that the workflow file is committed to the repository
- Ensure the workflow triggers on the branch you're protecting

## Verification

### Test the Protection Rules

1. Create a test branch:
   ```bash
   git checkout -b test-branch-protection
   ```

2. Make a small change (e.g., add a comment to a file)

3. Push and create a PR:
   ```bash
   git add .
   git commit -m "test: verify branch protection"
   git push origin test-branch-protection
   ```

4. Create a Pull Request on GitHub

5. Verify that:
   - ✅ The PR shows all required status checks
   - ✅ The "Merge" button is disabled until checks pass
   - ✅ You cannot merge without approval (if you're not the author)
   - ✅ After merging, the branch can be deleted

### Expected Behavior

**Before CI passes:**
- Merge button shows: "Merging is blocked: X checks have not passed"
- All required status checks show as "Required" with yellow/red indicators

**After CI passes:**
- All checks show green checkmarks
- Merge button becomes enabled (if review is approved)

**Without approval:**
- Merge button shows: "Merging is blocked: Review required"
- Even if CI passes, merge is blocked until review

## Status Check Names Reference

The following status checks are configured in `.github/workflows/exercise_11_ci.yml`:

| Job Name | Display Name | Purpose |
|----------|--------------|---------|
| `lint-backend` | Lint Backend (Python) | Runs flake8 and black checks |
| `type-check-backend` | Type Check Backend (Python) | Runs mypy type checking |
| `test-backend` | Unit Tests (Python) | Runs pytest unit tests |
| `lint-frontend` | Lint Frontend (TypeScript) | Runs ESLint and TypeScript checks |
| `test-e2e` | E2E Tests (Playwright) | Runs end-to-end Playwright tests |
| `build` | Build Docker Images | Builds backend and frontend Docker images |

## Troubleshooting

### Status Checks Not Appearing

**Problem**: Required status checks don't show up in the dropdown (shows "No required checks")

**This is the most common issue!** There are two common causes:

#### Cause 1: Checks Haven't Run Yet
GitHub only shows checks that have run at least once.

**Solution**:
1. **First, trigger the CI workflow** using one of the methods in the "Getting Checks to Appear" section above
2. Ensure the CI workflow file exists: `.github/workflows/exercise_11_ci.yml`
3. Wait for the workflow to **complete successfully** (not just started)
4. Wait 1-2 minutes after completion for GitHub to index the checks

#### Cause 2: You Need to Type the Job Names (Most Common!)
**IMPORTANT**: The search box does NOT auto-populate! You must **type each job name manually**.

**Solution**:
1. Click in the search box that says "Search for status checks in the last week for this repository"
2. **Type the exact job name** (e.g., `lint-backend`)
3. The check should appear as you type - click it to select
4. Repeat for each check:
   - `lint-backend`
   - `type-check-backend`
   - `test-backend`
   - `lint-frontend`
   - `test-e2e`
   - `build`

**If checks still don't appear after typing**:
- Verify the workflow ran successfully on the `main` branch (not just on PRs)
- Check workflow file syntax in `.github/workflows/exercise_11_ci.yml`
- Verify job names match exactly what you're typing
- Check the Actions tab to ensure workflow ran without errors
- Try refreshing the branch protection page

### Cannot Merge Even After Checks Pass

**Problem**: All checks pass but merge button is still disabled

**Possible causes**:
1. PR is not up to date with `main` - update/rebase the branch
2. Review not approved - get someone to approve the PR
3. Conversation not resolved - resolve any open comment threads
4. Branch protection rule misconfigured - review settings

### Admin Cannot Bypass Protection

**Problem**: Even repository admins cannot bypass protection rules

**Solution**:
- This is expected if "Do not allow bypassing the above settings" is enabled
- Temporarily disable this setting, or use a different branch for hotfixes
- Consider creating an exception rule for `hotfix/*` branches if needed

## Advanced Configuration

### Protecting Multiple Branches

You can create additional rules for:
- `develop` branch (same settings as `main`)
- `release/*` branches (stricter rules)
- `hotfix/*` branches (may allow bypass for urgent fixes)

### Code Owners

If you want to require specific reviewers based on file paths:

1. Create `.github/CODEOWNERS` file:
   ```
   # Backend code
   /exercise_11/backend/ @backend-team
   
   # Frontend code
   /exercise_11/frontend/ @frontend-team
   
   # Workflows
   /.github/workflows/ @devops-team
   ```

2. Enable "Require review from Code Owners" in branch protection

### Custom Status Checks

To require additional status checks (e.g., security scans):
1. Add the job to `.github/workflows/exercise_11_ci.yml`
2. Let it run at least once on a PR
3. Add it to the required status checks list

## Summary Checklist

After completing the setup, verify:

- [ ] Branch protection rule created for `main` branch
- [ ] All 6 CI status checks are required
- [ ] PR reviews required (minimum 1 approval)
- [ ] Branch deletion allowed
- [ ] Test PR created and verified protection works
- [ ] Merge button disabled until checks pass
- [ ] Merge button disabled until review approved

## Related Documentation

- [CI/CD Pipeline](../openspec/changes/add-cicd-pipelines/tasks.md)
- [Deployment Guide](./deployment.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
- [CI Workflow](../../.github/workflows/exercise_11_ci.yml)

## Next Steps

After configuring branch protection:

1. ✅ Update `exercise_11/openspec/changes/add-cicd-pipelines/tasks.md` to mark tasks 2.1-2.4 as complete
2. ✅ Test the workflow with a real PR
3. ✅ Document any team-specific exceptions or workflows
4. ✅ Consider protecting `develop` branch if you use a GitFlow workflow

---

**Last Updated**: After CI/CD pipeline implementation  
**Status**: Ready for configuration  
**Maintainer**: DevOps/Admin team

