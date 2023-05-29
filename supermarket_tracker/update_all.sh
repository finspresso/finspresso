#!/bin/bash

name=$1

echo "Collecting data with Selenium of type $name"
python supermarket_tracker.py --name $name --collect_products --take_screenshots

echo "Updating references/$name/product_reference.json"
python supermarket_tracker.py --name $name --update_reference_json latest

echo "Updating MySQL metadata table"
python supermarket_tracker.py --name $name --credentials_file credentials/sql_credentials.json --update_metadata_table

echo "Updating MySQL prices table"
python supermarket_tracker.py --name $name --credentials_file credentials/sql_credentials.json --update_prices_table
