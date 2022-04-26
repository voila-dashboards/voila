set -eux

git checkout stable || git checkout -b stable
git reset --hard origin/main

# Update the stable branch to point the latest release
if [[ ${RH_DRY_RUN:=true} != 'true' ]]; then
    git push origin stable -f
fi
