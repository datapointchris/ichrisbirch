## New Feature
If the feature is small make it an issue.
If the feature is large make it a milestone and break the steps into issues


## Bugs
1. Create an Issue
### Editor
1. `git checkout master`
2. `git pull`
3. `git checkout -b new-issue master`
4. `git add`
5. `git commit "Fixes # ___`
6. TEST to make sure it is fully working
7. `git checkout master`
8. `git pull`
9. `git merge new-issue`
11. `git push`
12. `git branch -d new-issue`