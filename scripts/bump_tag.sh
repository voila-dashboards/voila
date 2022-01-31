set -eux

# Update the stable tag to point the latest release
if [[ ${RH_DRY_RUN:=true} != 'true' ]]; then
    git tag -f -a stable -m "Github Action release"
    git push origin -f --tags
fi
