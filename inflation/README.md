# Inflation tracker

Tries to evaluate different inflation metrics.

# How to install the inflation tracker

Install Python packages requirements:

```sh
pip install -r requirements.txt
```

# How to run the inflation tracker

To start the inflation tracker, run the following:

```sh
python inflation_tracker --lik_data data/lik.xlsx
```

## Swiss inflation shown by LIK

The so-called LIK tab as shown below, visualizes the different weights of the inflation indicator Landesindex der Konsumentenpreise (LIK) for years between 2000 and 2022. The LIK measures as an index measures the price evolution of different goods in Switzerland. The source of this data is a .xlsx data sheet provided by the Swiss authority from [BFS](https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/erhebungen/lik/warenkorb.assetdetail.21484892.html). In the lower plot, you can see the variation of each category's weight over time from 2000 to 2022.

![lik_screenshot](images/lik_screenshot2.png)

### Running LIK weight the visualization via webbrowser

To run the visualization GUI from which you can see the weights per year respectively the evolution of each category over period from 2000 to 2022 , open file with webbrowser:
`html/lik.html`

Please note, in order for the webbrowser to be able to access the data in the .json files in the folder `storage_json`, you need to run a local server that serves that files via https requests. To do so, the following worked for me:

- Set up an apache server on Ubuntu PC that serves https requests. Explained in [here](https://techexpert.tips/apache/enable-https-apache/). Please note, I selected the IP address `127.0.0.1` of the apache server. If you select an other IP, you need to adapt this number in the file `html/lik.html` accordingly.
- I had to set Access-Control-Allow-Origin (CORS) Headers in apache according to [this](https://ubiq.co/tech-blog/set-access-control-allow-origin-cors-headers-apache/)
- Finally, I created a soft link in the apache folder that points to the `storage_json` folder of this repo: `sudo ln -s $PWD/html/storage_json_inflation /var/www/html/storage_json_inflation`. Please note, in order for this to work it is required that any parent path in the directory $PWD/html/storage_json needs to be accessible by any other user i.e. `drwxr-x--x`. Please be careful by changing the permission of your folder structure in order to prevent any security breach. If for testing purposes only you can always copy the folder storage_json to `/var/www/html/`.

Afterwards, if you open up `html/lik.html` via your webbrower it should look like below. In the dropdown menu you can select the desired year e.g. 2022 for the pie chart. In the lower plot you can see how the selected category's weight changed over time:

![LIKGIF](images/lik_weight_html.gif)

### Running LIK evolution the visualization via webbrowser

If you want to run the LIK evolution GUI in the webbrowser you can use the file [lik_evolution.html](html/mysql/lik_evolution.html). For that to work locally you need the following:

- Install XAMPP server
- Create new database
- Make .php files accessible to local XAMPP server
- Upload the LIK evolution data to the local MySQL database

#### Intall XAMPP server

Since I use a Linux computer, I used this [installation](https://vitux.com/ubuntu-xampp/) procedure to install the XAMPP server. The XAMPP server normally can be started by typing:

```sh
sudo /opt/lampp/manager-linux-x64.run
```

Afterwards, the XAMPP GUI should open up and you should be able to start all the servers.

![lampp](images/lampp.png)

#### Create new MySQL database

Once the XAMPP server is running you should be able to create the database via e.g. phpMyAdmin. The installation instruction for phpMyAdmin e.g. for Ubuntu 20.04 are given [here](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-phpmyadmin-on-ubuntu-20-04). To access the MySQL database via phpMyAdmin, type the following in your browser:

```sh
http://localhost/phpmyadmin/
```

Afterwards you can click on new and create your desired database:

![new_db](images/new_db.png)

### Make .php files accessible to local XAMPP server

In order for the XAMPP server to be able to respond to the request sent out by [lik_evolution.html](html/mysql/lik_evolution.html), you need to create a softlink to all the files in the html/mysql folder in the XAMPP base folder:

```sh
sudo mkdir /opt/lampp/htdocs/projects/
sudo ln -s <base folder of repo>/finspresso/inflation/html/mysql /opt/lampp/htdocs/projects/mysql
```

### Upload the LIK evolution data to the local MySQL database

- Download the data i.e. the .xlsx file and from the BFS site [here](https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/landesindex-konsumentenpreise/detailresultate.assetdetail.23925501.html). Create a file called sql_credentials.json that contains the credentials of the database. An example can be found in [sql_credentials_test.json](sql_credentials_test.json).

```sh
python inflation_tracker.py  --lik_evolution <Path to .xlsx file> --credentials_file sql_credentials.json --upload_to_sql
```

#### Accessing the LIK evolution GUI in the browser

Once the above steps have been completed you can open the the file [lik_evolution.html](html/mysql/lik_evolution.html) with your browser. You should see the following windows in which you can play around with all the LIK categories and different time periods:

![lik_evolution_gif](images/lik_evolution.gif)

## Create translation files

- Run lupdate:

```sh
make generate_ts_files
```

- Make your translation in the inflation_en.ts file e.g. with [Qt Linguist](https://doc.qt.io/qt-5/linguist-translators.html)

- Run lrelease

```sh
make generate_qm_files
```
