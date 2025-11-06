#!/bin/bash

# Stage all changed files
git add .

# Commit with fixed message
git commit -m "new changes on the arc agents"

# Get the current branch name
branch=$(git symbolic-ref --short HEAD)

# Push to the remote branch
git push origin "$branch"
