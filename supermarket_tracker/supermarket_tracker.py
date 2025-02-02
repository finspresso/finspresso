import argparse
import json
import logging
import coloredlogs
import datetime
import numpy as np
import pandas as pd
import re
import time


from collections import Counter
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from PIL import Image
from io import BytesIO

from db_interface.db_interface import DBInterface


logger = logging.getLogger("supermarket_tracker")
coloredlogs.install(level=logging.INFO)


class SuperMarketTracker:
    def __init__(self, name, data_folder, take_screenshots=False, interactive=True):
        self.name = name
        self.interactive = interactive
        self.data_folder = data_folder
        self.reference_folder = Path("references") / Path(name)
        self.take_screenshots = take_screenshots
        logger.debug("Init super market tracker with name %s", name)
        self.get_latest_collection_folder()
        self.load_config()

    def get_latest_collection_folder(self):
        self.latest_collection_file = "NA"
        download_folder = Path(self.data_folder) / Path(self.name)
        date_folder_list = []
        for path in download_folder.iterdir():
            if path.is_dir():
                match = re.search("[0-9]{8}", path.name)
                if match:
                    date_folder_list.append(path.name)
        if len(date_folder_list) > 0:
            date_folder_list.sort()
            self.latest_collection_file = (
                download_folder
                / Path(date_folder_list[-1])
                / Path(self.name + "_prices.xlsx")
            )

    def load_config(self):
        file_path = Path("configs") / Path(self.name + ".json")
        logger.debug("Loading config %s", file_path)
        with file_path.open("r") as file:
            self.config = json.load(file)

    def get_product_category(self, product_id):
        product_category = self.config["default_category"]
        for category, mask in self.config["categories"].items():
            if mask != "default":
                match = re.search(mask, product_id)
                if match:
                    product_category = category
                    break
        return product_category

    def collect_products(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        self.download_dict = dict()
        now = datetime.datetime.now()
        download_folder = (
            Path(self.data_folder)
            / Path(self.name)
            / Path(now.strftime("%Y%m%d_%H%M%S"))
        )
        download_folder.mkdir()
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        self.max_window_height = driver.get_window_size()["height"]
        self.current_offset = 0
        driver.get(self.config["collection_url"])
        try:
            extension_button_counter = 0
            while True:
                try:
                    xpath_extension_button = "/html/body/app-root/div[1]/lsp-shop/div/div/div/div/ng-component/main/div/div/div/div/div[2]/div/mo-items-display-view-more-btn/div/a"
                    logger.info("Searching for extension button")
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                xpath_extension_button,
                            )
                        )
                    )
                    logger.info("Clicking on extension button")
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(3)
                    extension_button_counter += 1
                except (TimeoutException, NoSuchElementException):
                    if extension_button_counter == 0:
                        logger.error("Zero extension button found. Aborting")
                        exit(1)
                    logger.info(
                        f"Pressed {extension_button_counter} extension buttons."
                    )
                    break
            try:
                logger.info("Searching for cookie banner")
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "/html/body/app-root/lsp-cookie-banner/section/div/button",
                        )
                    )
                )
                logger.info("Clicking away cookie banner")
                driver.execute_script("arguments[0].click();", element)
                time.sleep(4)
            except (TimeoutException, NoSuchElementException):
                logger.warning("No cookie banner found. Proceeding.")
            elements = driver.find_elements(By.TAG_NAME, "article")
            product_dict = dict()
            for element in elements:
                try:
                    product_id = "NA"
                    product_link = "NA"
                    product_name = "NA"
                    product_price = "NA"
                    subelement = element.find_element(
                        By.CLASS_NAME, "show-product-image"
                    )
                    product_link = subelement.get_attribute("href")
                    match = re.search("([0-9]+)", product_link)
                    if match:
                        product_id = match.group(1)
                        product_category = self.get_product_category(product_id)
                    else:
                        logger.error(
                            "Cannot extract product ID from link %s", product_link
                        )
                        continue

                    description_element = element.find_element(
                        By.XPATH,
                        ".//div/div[1]/a[2]/span[2]/lsp-product-name/div/span[2]",
                    )

                    span_elements = description_element.find_elements(
                        By.TAG_NAME, "span"
                    )
                    if len(span_elements):
                        product_name = " - ".join(
                            [span_element.text for span_element in span_elements]
                        )

                    subelement = element.find_element(
                        By.XPATH,
                        ".//div/div[1]/a[2]/span[2]/lsp-product-price/span/span/span",
                    )
                    match = re.search("([0-9]*\.[0-9]*)", subelement.text)
                    if match:
                        product_price = float(match.group(1))
                    else:
                        logger.error(
                            "Could not extract price for product %s", product_name
                        )
                    logger.info(
                        "%s, %s, %s, %s, %s",
                        product_id,
                        product_link,
                        product_name,
                        product_price,
                        product_category,
                    )
                    if self.take_screenshots:
                        self.get_element_screenshot(
                            driver, element, download_folder / Path(product_id + ".png")
                        )
                    product_dict[product_id] = [
                        product_link,
                        product_name,
                        product_price,
                        product_category,
                    ]
                except NoSuchElementException:
                    logger.warning(
                        "NoSuchElementException error occurred. Ignoring element."
                    )
        finally:
            driver.quit()
        df = pd.DataFrame.from_dict(product_dict, orient="index")
        df.columns = ["Product Link", "Product Name", "Price", "Category"]
        df.to_excel(download_folder / Path("mbudget_prices.xlsx"))
        delta = datetime.datetime.now() - now
        logger.info("Total download took %ss", round(delta.total_seconds(), 1))
        self.compare_to_reference(df)

    def compare_to_reference(self, df):
        new_articles = set()
        discontinued_articles = set()
        reference_json = self.reference_folder / Path("product_reference.json")
        if reference_json.exists():
            logger.info("Reference file %s exists", reference_json)
            with reference_json.open(mode="r") as file_input:
                reference = json.load(file_input)
                dict_reference = reference["Products"]
                reference_set = set(dict_reference.keys())
                active_set = set(
                    [
                        article
                        for article in dict_reference.keys()
                        if dict_reference[article]["Discontinued"] == "NA"
                    ]
                )
                downloaded_set = set(df.index.values)
                discontinued_articles = active_set - downloaded_set
                if len(discontinued_articles) == 0:
                    logger.info("No articles are discontinued")
                else:
                    logger.info(
                        "Labelled %s discontinued articles", len(discontinued_articles)
                    )
                    for article in discontinued_articles:
                        logger.warning(
                            "Discontinued article:\n\
                                        Product Link:%s\n\
                                        Product Name:%s\n\
                                        Price:%s\n\
                                        Category:%s\n",
                            dict_reference[article]["Product Link"],
                            dict_reference[article]["Product Name"],
                            dict_reference[article]["Price"],
                            dict_reference[article]["Category"],
                        )
                        logger.warning("Article %s discontinued", article)
                new_articles = downloaded_set - reference_set
                if len(new_articles) == 0:
                    logger.info("No new articles found")
                else:
                    logger.info("Found %s new articles", len(new_articles))
                    for article in new_articles:
                        logger.warning("New article: \n%s\n", df.loc[article, :])

        else:
            logger.error(
                "Reference json %s does not exist. Please provide this file",
                reference_json,
            )
        return discontinued_articles, new_articles

    def get_element_screenshot(self, driver, element, screenshot_name):
        driver.execute_script("arguments[0].scrollIntoView()", element)
        location = element.location
        size = element.size
        left = location["x"]
        top = location["y"]
        right = location["x"] + size["width"]
        bottom = location["y"] + size["height"]
        screenshot = driver.get_screenshot_as_png()
        im = Image.open(BytesIO(screenshot))
        im = im.crop((left, top, right, bottom))
        im.save(screenshot_name)

    @staticmethod
    def get_str_from_timestamp(timestamp):
        timestamp_string = "NA"
        if isinstance(timestamp, pd.Timestamp):
            timestamp_string = timestamp.strftime("%Y-%m-%d")
        return timestamp_string

    @staticmethod
    def check_for_duplicate_names(dict_reference, interactive):
        non_unique_name_dict = SuperMarketTracker.get_non_unique_names(dict_reference)
        n_non_unique = len(non_unique_name_dict)
        logger.info("Found %s non-unique article names", n_non_unique)
        counter = 0
        for non_unique_name, articles in non_unique_name_dict.items():
            counter += 1
            logger.info("%s/%s", counter, n_non_unique)
            logger.info(
                f"The articles {articles} have all the product name {non_unique_name}"
            )
            counter_article = 0
            for article_non_unique in articles:
                counter_article += 1
                product_link = dict_reference[article_non_unique]["Product Link"]
                if interactive:
                    input_string = (
                        f"Please provide new product name for {product_link}\n"
                    )
                    new_name = input(input_string)
                else:
                    new_name = non_unique_name + " " + str(counter_article)
                logger.info(
                    "Giving name %s to article %s", new_name, article_non_unique
                )

                dict_reference[article_non_unique]["Product Name"] = new_name

        return dict_reference

    @staticmethod
    def get_non_unique_names(dict_reference):
        product_names = [
            product_dict["Product Name"] for product_dict in dict_reference.values()
        ]
        non_unique_names = [k for k, v in Counter(product_names).most_common() if v > 1]
        non_unique_name_dict = dict()
        for name in non_unique_names:
            non_unique_name_dict[name] = tuple(
                article
                for article, product_dict in dict_reference.items()
                if product_dict["Product Name"] == name
            )
        return non_unique_name_dict

    def create_reference_json(self):
        product_sorted_xlsx = self.reference_folder / Path("product_sorted.xlsx")
        if product_sorted_xlsx.exists():
            logger.info("Reference file %s exists", product_sorted_xlsx)
            df_ref = pd.read_excel(product_sorted_xlsx, index_col=0)
            df_ref["Introduced"] = df_ref["Introduced"].map(self.get_str_from_timestamp)
            df_ref["Discontinued"] = df_ref["Discontinued"].map(
                self.get_str_from_timestamp
            )
            df_ref["Include"] = "Yes"
            dict_reference = df_ref.to_dict(orient="index")
            dict_reference = SuperMarketTracker.check_for_duplicate_names(
                dict_reference, self.interactive
            )
            reference_json = self.reference_folder / Path("product_reference.json")
            with reference_json.open(mode="w") as outfile:
                json.dump(dict_reference, outfile, indent=4, ensure_ascii=False)
                logger.info("Created %s.", reference_json)
        else:
            logger.error(
                "Reference file %s does not exist. Please provide this file",
                product_sorted_xlsx,
            )

    def update_reference_json(
        self, df, discontinued_articles, new_articles, update_date
    ):
        df_new_articles = df.loc[new_articles, :]
        reference_json = self.reference_folder / Path("product_reference.json")
        if reference_json.exists():
            logger.info("Reference file %s exists", reference_json)
            dict_reference = dict()
            with reference_json.open(mode="r") as file:
                reference = json.load(file)
                reference["Date"] = update_date
                dict_reference = reference["Products"]
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                for article in dict_reference.keys():
                    if article in df.index:
                        dict_reference[article]["Price"] = df.loc[article, "Price"]
                    else:
                        dict_reference[article]["Price"] = "NA"
                for article in discontinued_articles:
                    dict_reference[article]["Discontinued"] = today
                if not df_new_articles.empty:
                    df_new_articles["Introduced"] = today
                    df_new_articles["Discontinued"] = "NA"
                    new_articles_dict = df_new_articles.to_dict(orient="index")
                    df_new_articles["Include"] = "Yes"
                    if self.interactive:
                        df_new_articles["Category"] = "NA"
                        for article in new_articles_dict.keys():
                            product_name = new_articles_dict[article]["Product Name"]
                            product_link = new_articles_dict[article]["Product Link"]
                            input_string = f"New product {product_name} ({product_link}) detected.\nType g for grocery and o for other\n"
                            input_cat = input(input_string)
                            if input_cat == "g":
                                new_articles_dict[article]["Category"] = "grocery"
                            elif input_cat == "o":
                                new_articles_dict[article]["Category"] = "other"
                            else:
                                logger.error(
                                    "Unknown category input %s. Aborting", input_cat
                                )
                                exit(1)
                            input_string = f"New product {product_name} ({product_link}) detected.\nType y for include attribute and n for not\n"
                            input_cat = input(input_string)
                            if input_cat == "y":
                                new_articles_dict[article]["Include"] = "Yes"
                            elif input_cat == "n":
                                new_articles_dict[article]["Include"] = "No"
                            else:
                                logger.error(
                                    "Unknown include input %s. Aborting", input_cat
                                )
                                exit(1)
                    else:
                        for article in new_articles_dict.keys():
                            product_name = new_articles_dict[article]["Product Name"]
                            product_link = new_articles_dict[article]["Product Link"]
                            product_category = new_articles_dict[article]["Category"]
                            logger.info(
                                "Adding product: %s\nLink: %s\nCategory: %s",
                                product_name,
                                product_link,
                                product_category,
                            )
                    dict_reference.update(new_articles_dict)

                dict_reference = SuperMarketTracker.check_for_duplicate_names(
                    dict_reference, self.interactive
                )
                reference["Products"] = dict_reference

            if len(dict_reference) > 0:
                with reference_json.open(mode="w") as outfile:
                    json.dump(reference, outfile, indent=4, ensure_ascii=False)
                    logger.info("Updated %s", reference_json)
        else:
            logger.error(
                "Reference file %s does not exist. Please provide this file",
                reference_json,
            )

    def update_metadata_table(self, credentials):
        self.db_interface = DBInterface(credentials=credentials, print_all_tables=False)
        table_name = self.name + "_metadata"
        self.db_interface.delete_tables([table_name])
        reference_json = self.reference_folder / Path("product_reference.json")
        if reference_json.exists():
            logger.info("Reference file %s exists", reference_json)
            dict_reference = dict()
            with reference_json.open(mode="r") as file:
                reference = json.load(file)
                dict_reference = reference["Products"]
                df = pd.DataFrame.from_dict(dict_reference, orient="index")
                df.drop(labels="Price", axis=1, inplace=True)
                df.index.name = "Article"
                df.reset_index(inplace=True)
                type_dict = self.db_interface.infer_sqlalchemy_datatypes(df)
                self.db_interface.create_table_with_types(
                    table_name, df.columns, type_dict
                )
                logger.info(
                    "Re-creating SQL table %s in db %s",
                    table_name,
                    credentials["db_name"],
                )
                self.db_interface.connect()
                df.to_sql(
                    table_name,
                    con=self.db_interface.conn,
                    if_exists="append",
                    chunksize=1000,
                    dtype=type_dict,
                    index=False,
                )
                self.db_interface.close()
        else:
            logger.error("Reference file %s does not exist", reference_json)

    def update_prices_table(self, credentials):
        self.db_interface = DBInterface(credentials=credentials, print_all_tables=False)
        table_name = self.name + "_prices"
        existing_columns = set(self.db_interface.get_all_columns(table_name))

        table_name = self.name + "_prices"
        reference_json = self.reference_folder / Path("product_reference.json")
        if reference_json.exists():
            logger.info("Reference file %s exists", reference_json)
            dict_reference = dict()
            with reference_json.open(mode="r") as file:
                reference = json.load(file)
                dict_reference = reference["Products"]
                price_dict = {
                    article: article_dict["Price"]
                    for article, article_dict in dict_reference.items()
                }
                df = pd.DataFrame(
                    price_dict,
                    index=[datetime.datetime.strptime(reference["Date"], "%Y-%m-%d")],
                )
                grocery_cols = [
                    x
                    for x in df.columns
                    if dict_reference[x]["Category"] == "grocery"
                    and dict_reference[x]["Category"] != "NA"
                ]
                other_cols = [
                    x
                    for x in df.columns
                    if dict_reference[x]["Category"] == "other"
                    and dict_reference[x]["Category"] != "NA"
                ]
                df.insert(
                    0,
                    "Average other",
                    df.loc[:, other_cols].mean(axis=1, numeric_only=True),
                )
                df.insert(
                    0,
                    "Average grocery",
                    df.loc[:, grocery_cols].mean(axis=1, numeric_only=True),
                )
                df.insert(0, "Average overall", df.mean(axis=1, numeric_only=True))
                df.index.name = "Date"
                df.reset_index(inplace=True)
                type_dict = self.db_interface.infer_sqlalchemy_datatypes(df)
                if table_name in self.db_interface.get_all_tables():
                    existing_columns = set(
                        self.db_interface.get_all_columns(table_name)
                    )
                    new_columns = set(df.columns) - existing_columns
                    if len(new_columns) > 0:
                        self.db_interface.add_new_columns(
                            table_name, new_columns, type_dict
                        )
                else:
                    logger.info("Creating table %s", table_name)
                    self.db_interface.create_table_with_types(
                        table_name, df.columns, type_dict
                    )
                logger.info(
                    "Updating SQL table %s in db %s",
                    table_name,
                    credentials["db_name"],
                )
                self.db_interface.connect()
                df.replace("NA", np.nan, inplace=True)
                df.to_sql(
                    table_name,
                    con=self.db_interface.conn,
                    if_exists="append",
                    chunksize=1000,
                    dtype=type_dict,
                    index=False,
                )
                self.db_interface.close()
        else:
            logger.error("Reference file %s does not exist", reference_json)

    def print_prices_table(self, credentials):
        self.db_interface = DBInterface(credentials=credentials, print_all_tables=False)
        table_name = self.name + "_prices"
        self.db_interface.print_all_records(table_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        help="Sets the name of of the tracking category to consider",
        default="mbudget",
    )
    parser.add_argument(
        "--data_folder", help="Name of root folder to store the data", default="data"
    )
    parser.add_argument(
        "--take_screenshots",
        help="If given screenshots are stored",
        action="store_true",
    )
    parser.add_argument(
        "--collect_products",
        help="If selected, creates list with all products corresponding to config name",
        action="store_true",
    )
    parser.add_argument(
        "--create_reference_json",
        help="If selected it creates a reference json file containing the existing products.\
              The source for the creation is .xlsx file that must reside in the folder \
              references/<name>/product_sorted.xlsx",
        action="store_true",
    )
    parser.add_argument(
        "--update_reference_json",
        help="If selected it compares the reference json with the input xlsx file",
        type=str,
        default="",
    )
    parser.add_argument(
        "--credentials_file",
        help="Path to .json file containing db credentials",
        default="",
    )
    parser.add_argument(
        "--update_metadata_table",
        help="If given updates the metadata table of the product type e.g. MBudget",
        action="store_true",
    )
    parser.add_argument(
        "--update_prices_table",
        help="If given updates the prices table of the product type e.g. MBudget",
        action="store_true",
    )

    parser.add_argument(
        "--print_prices_table",
        help="If given print the prices table of \
              the product type e.g. MBudget present\
              in the MYSQL database",
        action="store_true",
    )
    parser.add_argument(
        "--no_headless",
        help="If selected, opens up browser window",
        action="store_true",
    )
    parser.add_argument(
        "--non_interactive",
        help="If selected, no products are added without asking",
        action="store_true",
    )

    credentials_sql = dict()
    args = parser.parse_args()

    logger.info("Consider tracking category %s", args.name)
    interactive = True
    if args.non_interactive:
        interactive = False
        logger.info("Running in non-interactive mode")
    else:
        logger.info("Running in interactive mode")
    if args.credentials_file != "":
        credentials_sql = DBInterface.load_db_credentials(args.credentials_file)
    tracker_handler = SuperMarketTracker(
        args.name,
        args.data_folder,
        take_screenshots=args.take_screenshots,
        interactive=interactive,
    )
    headless = not args.no_headless
    if args.collect_products:
        tracker_handler.collect_products(headless=headless)
    if args.create_reference_json:
        tracker_handler.create_reference_json()
    if args.update_reference_json != "":
        collection_file = Path(args.update_reference_json)
        if args.update_reference_json == "latest":
            if tracker_handler.latest_collection_file != "NA":
                collection_file = tracker_handler.latest_collection_file
                logger.info("Taking latest collection file %s", collection_file)
            else:
                logger.error("No latest collection .xlsx found")
                exit(1)
        if collection_file.exists():
            logger.info("File %s exists", collection_file)
            match = re.search("(20[0-9]{2})([0-9]{2})([0-9]{2})", str(collection_file))
            if match is None:
                logger.error(
                    "Could not extract date of format YYYYMMDD from name %s",
                    collection_file,
                )
                exit(1)
            update_date = match.group(1) + "-" + match.group(2) + "-" + match.group(3)
            df = pd.read_excel(collection_file, index_col=0)
            df.index = df.index.map(lambda x: str(x))
            discontinued_articles, new_articles = tracker_handler.compare_to_reference(
                df
            )
            tracker_handler.update_reference_json(
                df,
                discontinued_articles,
                new_articles,
                update_date,
            )
        else:
            logger.error("File %s does not exist", collection_file)
    if args.update_metadata_table:
        if len(credentials_sql) == 0:
            logger.error(
                "No valid credentials given. Please provide a valid credentials file."
            )
            return -1
        tracker_handler.update_metadata_table(credentials_sql)
    if args.update_prices_table:
        if len(credentials_sql) == 0:
            logger.error(
                "No valid credentials given. Please provide a valid credentials file."
            )
            return -1
        tracker_handler.update_prices_table(credentials_sql)

    if args.print_prices_table:
        if len(credentials_sql) == 0:
            logger.error(
                "No valid credentials given. Please provide a valid credentials file."
            )
            return -1
        tracker_handler.print_prices_table(credentials_sql)


if __name__ == "__main__":
    main()
