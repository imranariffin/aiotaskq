set -ex
npm --version
npm install embedme 2> /dev/null > /dev/null
DOC=src/sample_apps/README.md
npm run update-docs -- $DOC

set +ex

echo "Expecting no *uncommitted* changes to $DOC, checking ..."
gitdiff=$(git diff -- $DOC)
if [ -z "$gitdiff" ]
then
    echo "Changes to $DOC was already committed. Good."
else
    echo "Missing changes to $DOC that are supposed to be commited:"
    set -ex
    git diff -- $DOC | cat
    set +ex
    echo "Please run 'npm run -- $DOC', verify the changes, and commit appropriately."
    exit 1
fi