import argparse
import pandas as pd
import logging
import coloredlogs
import datetime
import sys
import re
from pyqtgraph.Qt import QtGui, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)


QtCore.QT_TRANSLATE_NOOP("get_translation", "Nahrungsmittel und alkoholfreie Getränke")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Alkoholische Getränke und Tabak")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Wohnen und Energie")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Bekleidung und Schuhe")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Hausrat und Haushaltsführung")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Hausrat und laufende Haushaltführung")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Gesundheitspflege")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Verkehr")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Nachrichtenübermittlung")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Freizeit und Kultur")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Unterricht")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Erziehung und Unterricht")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Restaurants und Hotels")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Sonstige Waren und Dienstleistungen")


NAME_MAPPING_DICT = {
    "Hausrat und laufende Haushaltsführung": "Hausrat und Haushaltsführung",
    "Erziehung und Unterricht": "Unterricht",
}


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class LIK(QtGui.QWidget):
    def __init__(self, lik_source):
        QtGui.QWidget.__init__(self)
        self.trans = QtCore.QTranslator(self)
        if self.trans.load("translations/inflation.en.qm"):
            QtGui.QApplication.instance().installTranslator(self.trans)
        self.main_layout = QtGui.QVBoxLayout()

        self.setLayout(self.main_layout)
        self.main_dict = dict()
        self.main_dict["LIK2020"] = self.get_lik_data(lik_source, "LIK2020")
        self.main_dict["LIK2015"] = self.get_lik_data(lik_source, "LIK2015")
        self.main_dict["LIK2010"] = self.get_lik_data(
            lik_source,
            "LIK2010",
            index_col=3,
            start_row=4,
            column_row=2,
            level_col="Pos",
        )
        self.main_dict["LIK2005"] = self.get_lik_data(
            lik_source,
            "LIK2005",
            index_col=3,
            start_row=4,
            column_row=2,
            level_col="Pos",
        )
        self.main_dict["LIK2000"] = self.get_lik_data(
            lik_source,
            "LIK2000",
            index_col=2,
            start_row=4,
            column_row=2,
            level_col="Nr. ",
            create_level_col=True,
        )
        self.create_lik_dict()
        current_year = str(datetime.datetime.now().year)
        self.pie_chart_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.category_chart_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.create_year_combobox(
            sorted(self.lik_dict.keys(), reverse=True), current_year
        )
        self.create_language_combobox(["German", "English"], "German")
        self.update_pie_chart(current_year)
        self.create_category_combobox(self.lik_df.index, self.lik_df.index[0])
        self.update_category_chart()
        self.main_layout.addWidget(self.year_cb)
        self.main_layout.addWidget(self.language_cb)
        self.main_layout.addWidget(self.pie_chart_canvas)
        self.main_layout.addWidget(self.category_cb)
        self.main_layout.addWidget(self.category_chart_canvas)

    def create_year_combobox(self, cb_list, current_text):
        self.year_cb = QtGui.QComboBox()
        self.year_cb.addItems(cb_list)
        self.year_cb.currentTextChanged.connect(self.update_pie_chart)
        self.year_cb.setCurrentText(current_text)

    def create_language_combobox(self, cb_list, current_text):
        self.language_cb = QtGui.QComboBox()
        self.language_cb.addItems(cb_list)
        self.language_cb.currentTextChanged.connect(self.update_pie_chart)
        self.language_cb.setCurrentText(current_text)

    def create_category_combobox(self, cb_list, current_text):
        self.category_cb = QtGui.QComboBox()
        self.category_cb.addItems(cb_list)
        self.category_cb.currentTextChanged.connect(self.update_category_chart)
        self.category_cb.setCurrentText(current_text)

    def update_category_chart(self):
        selected_category = self.category_cb.currentText()
        x = self.lik_df.loc[selected_category].index
        y = self.lik_df.loc[selected_category].values
        self.category_chart_canvas.axes.cla()
        self.category_chart_canvas.axes.plot(x, y)
        self.category_chart_canvas.axes.set_xticks(x)
        # self.category_chart_canvas.axes.set_xticklabels(averaging_names)
        self.category_chart_canvas.axes.set_xlabel("Year")
        self.category_chart_canvas.axes.set_ylabel("%")
        self.category_chart_canvas.draw()

    def update_pie_chart(self, text):
        selected_year = str(self.year_cb.currentText())
        selected_language = str(self.language_cb.currentText())
        self.current_pie_data = self.lik_dict[selected_year]
        self.pie_chart_canvas.axes.cla()
        sizes = self.current_pie_data.values
        labels = self.current_pie_data.index.values
        labels_translated = self.translate_labels(labels, language=selected_language)
        self.pie_chart_canvas.axes.pie(
            sizes,
            labels=labels_translated,
            autopct="%1.1f%%",
            shadow=False,
            startangle=90,
        )
        self.pie_chart_canvas.axes.axis("equal")
        self.pie_chart_canvas.draw()

    def translate_labels(self, labels, language="English"):
        labels_translated = labels
        if language == "English":
            labels_translated = [self.get_translation(word) for word in labels]
        return labels_translated

    @staticmethod
    def qt_translate(context, word):
        return QtCore.QCoreApplication.translate(context, word)

    def get_translation(self, word):
        word_translated = self.qt_translate("get_translation", word)
        return word_translated

    def get_weights(self, df, level, year):
        weights = df[df["Level"] == level][year]
        return weights

    def create_lik_dict(self, level=2):
        self.lik_dict = dict()
        self.lik_df = pd.DataFrame()
        current_year = datetime.datetime.now().year
        for df in self.main_dict.values():
            years = [x for x in df.columns if type(x) is not str]
            for year in years:
                if year <= current_year:
                    self.lik_dict[str(int(year))] = df[df["Level"] == level][year]
                    self.lik_df[int(year)] = df[df["Level"] == level][year]
        self.lik_df = self.lik_df[self.lik_df.columns.sort_values()]

    def get_lik_data(
        self,
        source_file,
        sheet_name,
        index_col=5,
        start_row=4,
        column_row=2,
        level_col="Level",
        create_level_col=False,
    ):
        # Make interactive plot showing pie for LIK weights in 2015 and 2020. Use matplotlib pyqt integration https://www.pythonguis.com/tutorials/plotting-matplotlib/
        # 2. Make Pie chart's year combobox select between 2015 and 2022
        # 3. Add option to select which change was biggest
        df_raw = pd.read_excel(source_file, index_col=index_col, sheet_name=sheet_name)
        df = df_raw.iloc[start_row:, :]
        df.columns = self.transform_type(df_raw.iloc[column_row, :])
        if "2000/01" in df.columns:
            df.rename(columns={"2000/01": 2000}, inplace=True)
            df[2001] = df[2000]
        if create_level_col:
            df.loc[:, "Level"] = df[level_col].apply(self.check_for_level)
        else:
            df = df.rename(columns={level_col: "Level"})
        nan_index = df["Level"].isna().argmax()
        if nan_index > 0:
            df = df.iloc[:nan_index, :]
        df.index = df.index.map(self.remove_empty_spaces)

        return df

    @staticmethod
    def transform_type(column):
        column_cast = []
        for value in column:
            if type(value) is str:
                if (
                    re.search("[0-9]{4}", value)
                    and re.search("[a-zA-Z]|/", value) is None
                ):
                    column_cast.append(int(value))
                else:
                    column_cast.append(value)
            else:
                column_cast.append(value)
        return column_cast

    @staticmethod
    def check_for_level(x, level=2):
        mask = r"^[0-9]{1,2}\b$"
        match = re.search(mask, str(x))
        level_assigned = -1
        if match:
            level_assigned = level
        return level_assigned

    @staticmethod
    def remove_empty_spaces(value):
        return_value = value
        if isinstance(value, str):
            return_value = value.strip()
        return_value = NAME_MAPPING_DICT.get(return_value, return_value)
        return return_value


class InflationTracker(QtGui.QTabWidget):
    def __init__(self, parent=None, source_lik=""):
        super(InflationTracker, self).__init__(parent)
        self.lik = LIK(source_lik)
        self.addTab(self.lik, "LIK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lik_data",
        help="xlsx file containing LIK weights",
        default="data/lik.xlsx",  # ToDo: Automate downlaod of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/erhebungen/lik/warenkorb.assetdetail.21484892.html
    )

    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    inflation_tracker = InflationTracker(source_lik=args.lik_data)
    inflation_tracker.show()
    sys.exit(app.exec_())


# Next: English translation of dropdown for second plot + update README with plot and datasource

if __name__ == "__main__":
    main()
