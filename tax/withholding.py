import logging
import coloredlogs

coloredlogs.install()
logger_name = __name__ if __name__ != "__main__" else "witholding"
logger = logging.getLogger(logger_name)
logging.basicConfig(level=logging.DEBUG)


def main():
    logger.info("Hello I am main")


if __name__ == "__main__":
    main()
