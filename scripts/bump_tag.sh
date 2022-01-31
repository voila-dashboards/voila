set -eux

# Update the stable branch to point the latest release
if [[ ${RH_DRY_RUN:=true} != 'true' ]]; then
    git checkout stable
    git reset --hard origin/main
    git push origin stable -f
fi
