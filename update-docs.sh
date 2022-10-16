set -ex
npm --version
npx --version
npm install embedme 2> /dev/null > /dev/null

set +ex

gitdiff=$(git diff)
if [ -z "$gitdiff" ]
then
    expect_no_change=true
else
    expect_no_change=false
fi

npx embedme docs/DOCS.md

if [ "$expect_no_change" == "true" ]
then
    echo "Expecting no changes to docs, checking ..."
    gitdiff=$(git diff)
    if [ -z "$gitdiff" ]
    then
        echo "No changes to doc. Good."
    else
        echo "Detected some changes to doc, exiting with error."
        exit 1
    fi
else
    echo "Not checking for changes in docs. Good."
fi
