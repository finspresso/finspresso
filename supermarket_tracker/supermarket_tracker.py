import argparse

# from bs4 import BeautifulSoup

# import requests
import logging
import coloredlogs


coloredlogs.install()
logger = logging.getLogger("supermarket_tracker")
logging.basicConfig(level=logging.DEBUG)


# class DownloadHandler:
#     def __init__(
#         self,
#         index,
#         single_processing=False,
#         jobs=None,
#         file_name=DEFAULT_FILE_NAME,
#     ):
#         self.download_url = INDEX_MAPPING_DICT.get(index)
#         self.single_processing = single_processing
#         self.jobs = jobs
#         self.file_name = file_name

#     def get_constituents(self, cached=False):
#         if cached:
#             self.load_constituents()
#         else:
#             self.download_constituetns()

#     def load_constituents(self):
#         print("Loading constituents url from file {}".format(self.file_name))
#         self.constituents = dict()
#         with open(self.file_name, "r") as input_file:
#             loaded_dict = json.load(input_file)
#             self.constituents = {
#                 key: {"url": value.get("url", "")}
#                 for key, value in loaded_dict.items()
#             }

#     def download_constituetns(self):
#         page = requests.get(self.download_url)
#         soup = BeautifulSoup(page.content, "html.parser")
#         last_page = self.get_last_page_sequence(soup)
#         self.constituents = dict()
#         mask = '"/kurs/aktie/(.+)/">(.+)</a>'
#         for i in range(1, last_page + 1):
#             url = self.download_url + "col=&asc=0&fpage=" + str(i)
#             page = requests.get(url)
#             soup = BeautifulSoup(page.content, "html.parser")
#             for i in range(1, 6):
#                 results = soup.findAll("table", {"id": "ALNI" + str(i)})
#                 if results:
#                     break
#             for result in results:
#                 sub_results = result.find_all("td")
#                 for sub_result in sub_results:
#                     annotations = sub_result.find_all("a")
#                     for annotation in annotations:
#                         match = re.search(mask, str(annotation))
#                         if match:
#                             self.constituents[
#                                 " ".join(match.group(1).split("-")[:-1])
#                             ] = {
#                                 "url": "https://ch.marketscreener.com/kurs/aktie/"
#                                 + match.group(1)
#                             }
#                             break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        help="Sets the name of of the tracking category to consider",
        default="mbuget",
    )
    args = parser.parse_args()
    logger.info("Consider tracking category %s", args.name)

    # download_handler = DownloadHandler(
    #     args.index,
    #     single_processing=args.single_processing,
    #     jobs=args.jobs,
    #     file_name=args.file_name,
    # )


if __name__ == "__main__":
    main()
