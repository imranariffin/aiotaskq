new_version=$(git diff origin/main -- pyproject.toml | grep '^\+version' | tr -dc '0-9.')

if [ -z "$new_version" ]
then
    echo "Changes not meant as a new version. Aborting."
    exit
fi

old_version=$(git diff origin/main -- pyproject.toml | grep '^\-version' | tr -dc '0-9.')
echo "Changes meant as new a version (from $old_version to $new_version)"

current_git_branch=$(git branch | grep -e '^*\s.*' | cut -d" " -f2 | tr -d "\n")
is_main_branch=$(echo $current_git_branch | tr -d "\n" | grep -E "^(origin/)?main$")

if [[ -z "$is_main_branch" ]]
then
    echo "Not on \"origin/main\" branch [branch=$current_git_branch], creating custom dev version based on commit hash ..."
    git_short_commit_hash_int=$(git rev-parse --short=7 HEAD | python -c "import sys; print(int(input(), 16))")
    new_version_custom="$new_version.dev$git_short_commit_hash_int"
    sed -i "s/version = \"$new_version\"/version = \"$new_version_custom\"/" pyproject.toml

    repository="aiotaskqdev"
    download_index_url="https://test.pypi.org/simple/"
    export TWINE_PASSWORD=$PYPI_TOKEN_DEV

    trap "git checkout -- pyproject.toml" EXIT
else
    echo "On \"$current_git_branch\" branch"
    repository="aiotaskq"
    download_index_url="https://pypi.org/simple/"
    export TWINE_PASSWORD=$PYPI_TOKEN
fi

pip install build > /dev/null
pip install twine > /dev/null

rm -rf dist/
python -m build
python -m twine check --strict dist/*
python -m twine upload --repository $repository --non-interactive --config-file ./.pypirc --verbose dist/*

echo "You can now install aiotaskq==$new_version_custom from $repository using the following command"
echo "(Might need to wait for a few hours (~12 hours), see https://github.com/pypa/pypi-support/issues/235#issuecomment-592930117)"
echo "***"
echo "pip install --index-url $download_index_url --no-deps aiotaskq==$new_version_custom"
echo "***"
