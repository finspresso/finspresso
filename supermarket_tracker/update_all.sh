#!/bin/bash

name=$1
base_branch=${2:-master}
auto_upload=${3:-False}

echo "Base branch is $base_branch"

echo "Collecting data with Selenium of type $name"
python supermarket_tracker.py --name $name --collect_products --take_screenshots

echo "Updating references/$name/product_reference.json"
python supermarket_tracker.py --name $name --update_reference_json latest --non_interactive

echo "Updating MySQL metadata table"
python supermarket_tracker.py --name $name --credentials_file credentials/sql_credentials.json --update_metadata_table

echo "Updating MySQL prices table"
python supermarket_tracker.py --name $name --credentials_file credentials/sql_credentials.json --update_prices_table

git status | grep "product_reference.json"
if [ $? == "0" ]
then
    if [ "$auto_upload" = "True" ]
    then
        branch_name=$(date +%s)
        echo "Creating new branch with name $branch_name"
        git checkout -b $branch_name
    fi
    file_name="references/$name/product_reference.json"
    echo "Committing $file_name"
    pre-commit run --files $file_name
    git add $file_name
    git commit -m "Updating product_reference for $name"

    echo "Pushing changes"
    if [ "$auto_upload" = "True" ]
    then
        git push -u origin $branch_name
        gh pr create --title "Updating Mbudget" --base $base_branch --body "Updated product_reference.json"
    else
        git push
    fi
fi
