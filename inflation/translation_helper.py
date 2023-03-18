import argparse
import pandas as pd

from lxml import etree


class TranslationHelper:
    def __init__(self):
        pass

    @staticmethod
    def create_message_element(file_name, source_text, translation_text):
        message_element = etree.Element("message")
        location_element = etree.Element("location")
        location_element.set("filename", file_name)
        location_element.set("line", "1")
        message_element.append(location_element)
        source_element = etree.Element("source")
        source_element.text = source_text
        message_element.append(source_element)
        translation_element = etree.Element("translation")
        translation_element.text = translation_text
        message_element.append(translation_element)
        return message_element

    @staticmethod
    def create_ts_file(
        df_translation,
        csv_source_file="translation_inflation.csv",
        ts_file_name="translations/inflation.en.ts",
        context_name="inflation_tracker",
    ):
        root = etree.Element("TS")
        root.set("version", "2.1")
        root.set("language", "en_US")

        context = etree.SubElement(root, "context")
        name_element = etree.SubElement(context, "name")
        name_element.text = context_name
        file_name = "../inflation_tracker.py"
        for _, row in df_translation.iterrows():
            source_text = row["German"]
            translation_text = row["English"].capitalize()
            message_element = TranslationHelper.create_message_element(
                file_name, source_text, translation_text
            )
            context.append(message_element)
        etree.indent(root)
        b_xml = etree.tostring(
            root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )

        with open(ts_file_name, "wb") as f:
            f.write(b_xml)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--translation_csv",
        help="File containing strings to be indexed",
        default="translations/translation_inflation.csv",
    )
    args = parser.parse_args()

    df_translation = pd.read_csv(args.translation_csv)
    TranslationHelper.create_ts_file(df_translation)


if __name__ == "__main__":
    main()
