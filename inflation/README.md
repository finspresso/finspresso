# Inflation tracker (work in progress)
Tries to evaluate different inflation metrics

## Create translation files

* Run lupdate:
```sh
make generate_ts_files
```

* Make your translation in the inflation_en.ts file e.g. with [Qt Linguist](https://doc.qt.io/qt-5/linguist-translators.html)

* Run lrelease
```sh
make generate_qm_files
```
