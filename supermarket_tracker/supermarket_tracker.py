import argparse
import json
import logging
import coloredlogs
import datetime
import pandas as pd
import re
import time


from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


logger = logging.getLogger("supermarket_tracker")
coloredlogs.install(level=logging.INFO)


class SuperMarketTracker:
    def __init__(self, name, data_folder, take_screenshots=False):
        self.name = name
        self.data_folder = data_folder
        self.take_screenshots = take_screenshots
        logger.debug("Init super market tracker with name %s", name)
        self.load_config()

    def load_config(self):
        file_path = Path("configs") / Path(self.name + ".json")
        logger.debug("Loading config %s", file_path)
        with file_path.open("r") as file:
            self.config = json.load(file)

    def download_prices(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.download_dict = dict()
        now = datetime.datetime.now()
        download_folder = (
            Path(self.data_folder)
            / Path(self.name)
            / Path(now.strftime("%Y%m%d_%H%M%S"))
        )
        download_folder.mkdir()
        for product in self.config["products"]:
            product_id = product["id"]
            self.download_dict[product_id] = {"price": "NA", "name": product["name"]}
            url = self.config["base_url"] + "/" + product["id"]
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
            logger.info("Downloading product %s", product["name"])
            driver.get(url)
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "actual"))
                )
                self.download_dict[product_id]["price"] = element.text
                if self.take_screenshots:
                    driver.save_screenshot(download_folder / Path(product_id + ".png"))
            finally:
                driver.quit()
        logger.info(self.download_dict)

    def collect_products(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
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
        driver.get(self.config["collection_url"])
        try:
            while True:
                try:
                    logger.info("Searching for extension button")
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                '//*[@id="brand-search-products-content"]/div[2]/app-products-display/div[2]/div/button',
                            )
                        )
                    )
                    logger.info("Clicking on extension button")
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(3)
                except (TimeoutException, NoSuchElementException):
                    logger.warning("No extension button found. Proceeding.")
                    break
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
                    else:
                        logger.error(
                            "Cannot extract product ID from link %s", product_link
                        )
                        continue
                    subelement = element.find_element(
                        By.XPATH,
                        ".//div/div[1]/a[2]/span[1]/lsp-product-name/div/span[2]/span",
                    )
                    product_name = subelement.text
                    subelement = element.find_element(
                        By.XPATH,
                        ".//div/div[1]/a[2]/span[1]/lsp-product-price/span/span/span",
                    )
                    match = re.search("([0-9]*\.[0-9]*)", subelement.text)
                    if match:
                        product_price = float(match.group(1))
                    else:
                        logger.error(
                            "Could not extract price for product %s", product_name
                        )
                    logger.info(
                        "%s, %s, %s, %s",
                        product_id,
                        product_link,
                        product_name,
                        product_price,
                    )
                    product_dict[product_id] = [
                        product_link,
                        product_name,
                        product_price,
                    ]
                except NoSuchElementException:
                    logger.warning(
                        "NoSuchElementException error occurred. Ignoring element."
                    )
        finally:
            driver.quit()
        df = pd.DataFrame.from_dict(product_dict, orient="index")
        df.columns = ["Product Link", "Product Name", "Price"]
        df.to_excel("mbudget_prices.xlsx")


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
        "--download_prices",
        help="If selected, dowloads latest prices for all products corresponding to config name",
        action="store_true",
    )
    parser.add_argument(
        "--collect_products",
        help="If selected, creates list with all products corresponding to config name",
        action="store_true",
    )

    args = parser.parse_args()
    logger.info("Consider tracking category %s", args.name)
    logger.debug("Debug log line")
    tracker_handler = SuperMarketTracker(
        args.name, args.data_folder, take_screenshots=args.take_screenshots
    )
    if args.download_prices:
        tracker_handler.download_prices()
    if args.collect_products:
        tracker_handler.collect_products()


if __name__ == "__main__":
    main()
