# Super market trackers

Tracks prices of selected super market.

## Make .php files accessible to local XAMPP server

In order for th local XAMPP server to be able to respond to the request sent out by [supermarket_tracker.html](browser/html/supermarket_tracker.html), you need to create a softlink to all the files in the `browser/html` and `browser/php_files` folder in the XAMPP base folder (`/opt/lampp/htdocs/`):

```sh
sudo mkdir /opt/lampp/htdocs/supermarket_tracker
PROJECTS_FOLDER=<base folder of repo>
sudo ln -s $PROJECTS_FOLDER/finspresso/supermarket_tracker/browser/html /opt/lampp/htdocs/supermarket_tracker/html
sudo ln -s $PROJECTS_FOLDER/finspresso/supermarket_tracker/browser/php_files /opt/lampp/htdocs/supermarket_tracker/php_files
```

After that you should be able to open the supermarket_tracker.html with your browser e.g. with Chrome:

```sh
/opt/google/chrome/chrome http://localhost/inflation/html/supermarket_tracker.html
```

Please note, the Apache server will not execute the .php files and respond if you directly try to open the file lik_evolution.html with your browser that resides in the repo folder. Hence, important to copy both html and php_files folder. This [entry](https://github.com/finspresso/finspresso/tree/master/inflation#intall-xampp-server) shows how to install a LAMPP server.
