#!/bin/bash

BRANCH=$1
DELETE_BRANCH=false
MESSAGE=$1

if [[ $2 == "-d" ]]; then
  DELETE_BRANCH=true
fi

if [ -z "$BRANCH" ]; then
  echo "Please provide a branch name or a commit message.
  Simple Commit:......: ./commiter.sh 'Your message' to commit.
  Merge Main:.........: ./commiter.sh 'Your message' -m to merge to main branch.
  Specific Branch.....: ./commiter.sh 'Your message' -m 'branch' to merge to a specific branch.
  Delete Branch.......: ./commiter.sh 'branch-name' -d to delete the branch locally and remotely."
  exit 1
fi

if [ "$DELETE_BRANCH" = true ]; then
  git branch -d "$BRANCH" 2>/dev/null || git branch -D "$BRANCH"
  git push origin --delete "$BRANCH"
  echo "Branch '$BRANCH' deleted locally and remotely."
  exit 0
fi

if [[ $2 == "-m" ]]; then
  if [ -n "$3" ]; then
    TARGET_BRANCH=$3
  else
    TARGET_BRANCH="main"
  fi
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -z "$MESSAGE" ]; then
  echo "Please provide a commit message.
  Simple Commit:......: ./commiter.sh 'Your message' to commit.
  Merge Main:.........: ./commiter.sh 'Your message' -m to merge to main branch.
  Specific Branch.....: ./commiter.sh 'Your message' -m 'branch' to merge to a specific branch."
  exit 1
fi

git add . && git commit -am "[$CURRENT_BRANCH] $MESSAGE" && git push

if [ -n "$TARGET_BRANCH" ]; then
  git checkout "$TARGET_BRANCH"
  git merge "$CURRENT_BRANCH"
  git push
  git checkout "$TARGET_BRANCH"
fi
echo "Changes committed to branch '$CURRENT_BRANCH' with message: '$MESSAGE'."
if [ -n "$TARGET_BRANCH" ]; then
  echo "Merged changes into branch '$TARGET_BRANCH'."
else
  echo "No merge performed, committed to current branch '$CURRENT_BRANCH'."
fi
if [ -n "$TARGET_BRANCH" ]; then
  git checkout "$CURRENT_BRANCH"
fi
echo "Switched back to branch '$CURRENT_BRANCH'."