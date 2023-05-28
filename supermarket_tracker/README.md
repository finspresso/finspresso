# Super market trackers

Tracks prices of selected super market.

## MBudget tracker

The MBudget tracker collects all the available prices that can be accessed via the mbudget protuct overview [page](https://www.migros.ch/en/brand/m-budget). Please note, the correct url is given in the config `config/mbudget.json`. This page list all the available products and there price as e.g. shown below:

![mbudget_base](images/mbudget_base.png)

To start the collection of the product type:

```sh
python supermarket_tracker.py --name mbudget --collect_products --take_screenshots
```

This does the following:

- Opens the mbudget product overview [page](https://www.migros.ch/en/brand/m-budget) using the [Selium-Python](https://selenium-python.readthedocs.io/) library in headless mode
- Extracts the price, article number and product name and stores them into an .xlsx file in the folder `data/mbudget/<Date and time of run>/mbudget_prices.xlsx`
- Compares the downloaded products with the prior state stored in the folder `references/mbudget/product_reference.json` and list which products were added and which were discontinued.
- Additionally the script takes a screenshot of every product and stores the screenshots under `data/mbudget/<Date and time of run>/`

Please note, if you leave the option `--take_screenshots` the whole process takes significantly longer i.e. around 140s.

![collect](images/collect.png)

## Make .php files accessible to local XAMPP server

In order for th local XAMPP server to be able to respond to the request sent out by e.g. [mbudget_tracker.html](browser/html/mbudget_tracker.html), you need to create a softlink to all the files in the `browser/html` and `browser/php_files` folder in the XAMPP base folder (`/opt/lampp/htdocs/`):

```sh
sudo mkdir /opt/lampp/htdocs/supermarket_tracker
PROJECTS_FOLDER=<base folder of repo>
sudo ln -s $PROJECTS_FOLDER/finspresso/supermarket_tracker/browser/html /opt/lampp/htdocs/supermarket_tracker/html
sudo ln -s $PROJECTS_FOLDER/finspresso/supermarket_tracker/browser/php_files /opt/lampp/htdocs/supermarket_tracker/php_files
```

After that you should be able to open the mbudget_tracker.html with your browser e.g. with Chrome:

```sh
/opt/google/chrome/chrome http://localhost/supermarket_tracker/html/mbudget_tracker.html
```

Please note, the Apache server will not execute the .php files and respond if you directly try to open the file lik_evolution.html with your browser that resides in the repo folder. Hence, important to copy both html and php_files folder. This [entry](https://github.com/finspresso/finspresso/tree/master/inflation#intall-xampp-server) shows how to install a LAMPP server.
