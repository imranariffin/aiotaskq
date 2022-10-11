current_git_branch=$(git name-rev --name-only HEAD)
is_main_branch=$(echo $current_git_branch | tr -d "\n" | grep -E "^main$")
if [[ -z "$is_main_branch" ]]
then
    old_version=$(git diff origin/main -- pyproject.toml | grep '^\-version' | tr -dc '0-9.')
    new_version=$(git diff origin/main -- pyproject.toml | grep '^\+version' | tr -dc '0-9.')
else
    old_version=$(git diff HEAD~1 -- pyproject.toml | grep '^\-version' | tr -dc '0-9.')
    new_version=$(git diff HEAD~1 -- pyproject.toml | grep '^\+version' | tr -dc '0-9.')
fi

echo "On branch \"$current_git_branch\": old_version=\"$old_version\", new_version=\"$new_version\""

if [ -z "$new_version" ]
then
    echo "Changes not meant as a new version. Aborting."
    exit
fi
echo "Changes meant as new a version (from $old_version to $new_version)"

if [[ -z "$is_main_branch" ]]
then
    echo "Not on \"origin/main\" branch [branch=$current_git_branch], creating custom dev version based on commit hash ..."
    git_short_commit_hash_int=$(git rev-parse --short=7 HEAD | python -c "import sys; print(int(input(), 16))")
    new_version_custom="$new_version.dev$git_short_commit_hash_int"
    sed -i "s/version = \"$new_version\"/version = \"$new_version_custom\"/" pyproject.toml
    new_version=$new_version_custom

    repository="pypitest"
    download_index_url="https://test.pypi.org/simple/"
    export TWINE_PASSWORD=$PYPI_TOKEN_DEV

    trap "git checkout -- pyproject.toml" EXIT
else
    echo "On \"$current_git_branch\" branch"
    repository="pypi"
    download_index_url="https://pypi.org/simple/"
    export TWINE_PASSWORD=$PYPI_TOKEN
fi

echo "Installling build & twine ..."
pip install build > /dev/null
pip install twine > /dev/null

echo "Building aiotaskq==$new_version..."
rm -rf dist/
python -m build

echo "Uploading to $repository ..."
python -m twine check --strict dist/*
python -m twine upload --repository $repository --non-interactive --config-file ./.pypirc --verbose dist/*

echo "You can now install aiotaskq==$new_version from $repository using the following command"
if [ -z "$is_main_branch" ]
then
    echo "(Might need to wait for a few hours (~12 hours), see https://github.com/pypa/pypi-support/issues/235#issuecomment-592930117)"
fi
echo "***"
echo "pip install --index-url $download_index_url --no-deps aiotaskq==$new_version"
echo "***"
