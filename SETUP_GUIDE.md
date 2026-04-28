# Real World Setup Guide - Project 2

This is how a cloud engineer actually works day to day.
Follow this once and it becomes your muscle memory for every future project.

---

## Part 1: One-time setup on your laptop

### Install Git
Download from https://git-scm.com/download/win
Accept all defaults during installation.

Verify:
  git --version

### Install AWS SAM CLI (for local testing only)
  pip install aws-sam-cli
  sam --version

### Install Python 3.12
Download from https://www.python.org/downloads/
Check "Add Python to PATH" during installation.

---

## Part 2: Create your GitHub repository

1. Go to https://github.com and log in
2. Click the + button at the top right
3. Click "New repository"
4. Name it: serverless-task-api
5. Set it to Public (so recruiters can see it)
6. Do NOT add README or .gitignore (we have our own)
7. Click "Create repository"
8. Copy the repository URL (looks like: https://github.com/yourusername/serverless-task-api.git)

---

## Part 3: Add AWS credentials to GitHub Secrets

This is the critical security step. Your AWS keys go here, not in any file.

1. Go to your repository on GitHub
2. Click Settings (top tab)
3. Click Secrets and variables in the left menu
4. Click Actions
5. Click "New repository secret" and add these three secrets one by one:

   Name: AWS_ACCESS_KEY_ID
   Value: (your AWS access key from IAM)

   Name: AWS_SECRET_ACCESS_KEY
   Value: (your AWS secret key from IAM)

   Name: AWS_REGION
   Value: ap-south-1

How to get your AWS keys:
  AWS Console > IAM > Users > your user > Security credentials > Create access key
  Choose "Command Line Interface (CLI)" as the use case.

---

## Part 4: Create an IAM user for GitHub Actions (best practice)

Do not use your root account keys. Create a dedicated user for deployments.

In AWS Console > IAM > Users > Create user:
  Username: github-actions-deploy
  Attach policy: PowerUserAccess (for portfolio use)
  
In production teams this user would have a much tighter custom policy
(only SAM, CloudFormation, Lambda, API Gateway, DynamoDB, S3, IAM for roles).
For your portfolio, PowerUserAccess is fine.

Create access key for this user and use those values in GitHub Secrets.

---

## Part 5: Push your code and trigger the pipeline

Open PowerShell. Navigate to your project2 folder.

Initialize git and push:

  git init
  git add .
  git commit -m "Initial commit: Serverless Task API"
  git branch -M main
  git remote add origin https://github.com/YOURUSERNAME/serverless-task-api.git
  git push -u origin main

Create the dev branch:

  git checkout -b dev
  git push origin dev

Now your repository has two branches: main and dev.

---

## Part 6: Your daily workflow from now on

Every time you make a change:

  git checkout dev
  (make your code changes in VS Code)
  git add .
  git commit -m "describe what you changed"
  git push origin dev

GitHub Actions automatically triggers and deploys to AWS dev environment.
Watch it run at: https://github.com/YOURUSERNAME/serverless-task-api/actions

When dev is tested and working, merge to main:

  Go to GitHub > Pull requests > New pull request
  Base: main   Compare: dev
  Click "Create pull request"
  Add a description of what changed
  Click "Merge pull request"

GitHub Actions then deploys to prod automatically.

---

## Part 7: How to run tests locally before pushing

  cd project2 folder
  pip install pytest boto3
  pytest tests/ -v

Green = all good, push your code.
Red = fix the issue before pushing.

---

## Part 8: Protect the main branch (important habit)

On GitHub:
  Settings > Branches > Add branch ruleset
  Branch name pattern: main
  Check: Require a pull request before merging
  Check: Require status checks to pass (add your Actions workflow)

This means nobody - including you - can push directly to main.
Everything must go through a PR. This is the rule in every real team.

---

## What you can say in interviews

"I follow a GitFlow branching strategy. All feature work goes on dev,
gets reviewed via a Pull Request, and merges to main only after the
CI/CD pipeline passes. GitHub Actions handles the SAM build and deploy
to separate dev and prod CloudFormation stacks. AWS credentials are
stored as GitHub Secrets - never in code or config files."

That answer tells the interviewer you understand security, automation,
environment separation, and team collaboration - everything they look for.
