set -ex
npm --version
npm install embedme 2> /dev/null > /dev/null
npm run update-docs -- docs/DOCS.md

set +ex

echo "Expecting no *uncommitted* changes to docs/DOCS.md, checking ..."
gitdiff=$(git diff -- docs/DOCS.md)
if [ -z "$gitdiff" ]
then
    echo "Changes to doc/DOCS.md was already committed. Good."
else
    echo "Missing changes to docs/DOCS.md that are supposed to be commited:"
    set -ex
    git diff -- docs/DOCS.md | cat
    set +ex
    echo "Please run ./update-docs.sh, verify the changes & commit appropriately."
    exit 1
fi
