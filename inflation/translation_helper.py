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
        csv_source_file="translation_inflation.csv",
        ts_file_name="inflation.en.ts",
        context_name="inflation_tracker",
    ):
        root = etree.Element("context")
        context = etree.SubElement(root, "name")
        context.text = context_name
        translation_dict = {
            "Nahrungsmittel": "Food",
            "Reis": "Rice",
            "Teigewaren": "Pasta",
        }
        file_name = "../inflation_tracker.py"
        for source_text, translation_text in translation_dict.items():
            message_element = TranslationHelper.create_message_element(
                file_name, source_text, translation_text
            )
            root.append(message_element)
        etree.indent(root)
        b_xml = etree.tostring(
            root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )

        with open("GFG.xml", "wb") as f:
            f.write(b_xml)


def main():
    TranslationHelper.create_ts_file()


if __name__ == "__main__":
    main()
