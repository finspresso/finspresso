# Tax
This folder contains scripts that relate to pages with regards to taxes on www.finspresso.com.

## Installation
In order to be able to run the Python script, run:

`pip install -r requirements.txt`

`pre-commit install`

## Running the GUI
To run the GUI from which you can see the taxes respectively the tax rate per municipality run:
`python withholding.py`

This will open up the default GUI as shown below. In the dropdown menu you can select the desired municipality e.g. Seegräben. In the upper plot you can see how much tax you need to pay in total, for the municipality, canton and federal. In the lower plot you can see the tax rate per taxable income (x-axis).
![Tax](images/tax.png)

## Storing taxes to .json file
If you want to store all the tax data for all municipalities pf the canton of Zurich type:
`python withholding.py --json`

This will essentially create a .json file for every municipality containing the corresponding tax values per taxable income in the folder `storage_json`.
