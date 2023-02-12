import argparse
import json
from math import floor
import numpy as np

import pandas as pd
import logging
import coloredlogs
import datetime
import sys
import re
from pathlib import Path
from pyqtgraph.Qt import QtGui, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from db_interface import DBInterface

# Global settings
coloredlogs.install()
logger = logging.getLogger("portfolio_tracker")
logging.basicConfig(level=logging.DEBUG)

trans = QtCore.QTranslator()


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
QtCore.QT_TRANSLATE_NOOP("get_translation", "Obligatorische Krankenpflegeversicherung")
QtCore.QT_TRANSLATE_NOOP("get_translation", "Krankenzusatzversicherung")


NAME_MAPPING_DICT = {
    "Hausrat und laufende Haushaltsführung": "Hausrat und Haushaltsführung",
    "Hausrat und laufende Haushaltführung": "Hausrat und Haushaltsführung",
    "Erziehung und Unterricht": "Unterricht",
}

LIK_CATEGORY_LIST = [
    "Nahrungsmittel und alkoholfreie Getränke",
    "Alkoholische Getränke und Tabak",
    "Wohnen und Energie",
    "Bekleidung und Schuhe",
    "Hausrat und Haushaltsführung",
    "Hausrat und laufende Haushaltführung",
    "Gesundheitspflege",
    "Verkehr",
    "Nachrichtenübermittlung",
    "Freizeit und Kultur",
    "Unterricht",
    "Erziehung und Unterricht",
    "Restaurants und Hotels",
    "Sonstige Waren und Dienstleistungen",
    "Total",
]


def get_last_date_of_month(year, month):
    """Return the last date of the month.

    Args:
        year (int): Year, i.e. 2022
        month (int): Month, i.e. 1 for January

    Returns:
        date (datetime): Last date of the current month
    """

    if month == 12:
        last_date = datetime.datetime(year, month, 31)
    else:
        last_date = datetime.datetime(year, month + 1, 1) + datetime.timedelta(days=-1)

    return last_date


def create_color_dict(init_value=12345):
    rng = np.random.default_rng(init_value)
    colors = rng.uniform(0, 1, (len(LIK_CATEGORY_LIST), 3))
    color_dict = {
        LIK_CATEGORY_LIST[i]: colors[i, :] for i in range(len(LIK_CATEGORY_LIST))
    }
    return color_dict


def create_RGB_dict_javascript(color_dict_rgb):
    color_dict_rgb_javascript = dict()

    for category, color in color_dict_rgb.items():
        if category not in color_dict_rgb_javascript.keys():
            javascript_string = (
                "rgb("
                + str(floor(255 * color[0]))
                + ","
                + str(floor(255 * color[1]))
                + ","
                + str(floor(255 * color[2]))
                + ")"
            )
            color_dict_rgb_javascript[
                NAME_MAPPING_DICT.get(category, category)
            ] = javascript_string
    return color_dict_rgb_javascript


def qt_translate(context, word):
    return QtCore.QCoreApplication.translate(context, word)


def setup_translation():
    global trans
    if trans.load("translations/inflation.en.qm"):
        QtGui.QApplication.instance().installTranslator(trans)


def translate_labels(labels, language="English"):
    labels_translated = labels
    if language == "English":
        labels_translated = [qt_translate("get_translation", word) for word in labels]
    return labels_translated


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class KVPI(QtGui.QTabWidget):
    def __init__(
        self,
        source_kvpi_evolution="",
        current_language="",
    ):
        super().__init__()
        df_kvpi = self.get_kvpi_data(source_kvpi_evolution)
        self.kvpi_weights = KVPIWeights(df_kvpi, current_language)
        self.kvpi_evolution = KVPIEvolution(df_kvpi, current_language)
        self.addTab(self.kvpi_weights, "Weights")
        self.addTab(self.kvpi_evolution, "Evolution")

    def get_kvpi_data(self, source_file):
        logger.info("Loading %s... for KPVI", source_file)
        df_raw = pd.read_excel(source_file)
        df_kvpi = pd.DataFrame(
            index=df_raw.iloc[5:29, 0],
            columns=[
                "Total",
                "Obligatorische Krankenpflegeversicherung",
                "Krankenzusatzversicherung",
            ],
            data=df_raw.iloc[5:29, 1:4].values,
        )
        return df_kvpi


class KVPIWeights(QtGui.QWidget):
    def __init__(self, df_kvpi, current_language):
        QtGui.QWidget.__init__(self)
        self.current_language = current_language
        self.compute_kvpi_weights(df_kvpi)

    def compute_kvpi_weights(self, df_kvpi):
        self.df_kvpi_weights = pd.DataFrame(
            columns=df_kvpi.columns[1:], index=df_kvpi.index
        )
        self.df_kvpi_weights.iloc[:, 0] = df_kvpi.apply(
            self.get_weights_per_year, axis=1
        )
        self.df_kvpi_weights.iloc[:, 1] = 1 - self.df_kvpi_weights.iloc[:, 0]

    def get_weights_per_year(self, row):
        total = row[0]
        x1 = row[1]
        x2 = row[2]
        weight = 2 / 3
        if x1 != x2:
            weight = (total - x2) / (x1 - x2)
        return weight


class KVPIEvolution(QtGui.QWidget):
    def __init__(self, df_kvpi, current_language):
        QtGui.QWidget.__init__(self)
        self.df_kvpi_evolution = df_kvpi.copy()
        self.translated_index = self.df_kvpi_evolution.columns.values.tolist()
        self.current_language = current_language
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.kvpi_chart_canvas = MplCanvas(self, width=5, height=6, dpi=100)
        self.create_category_combobox_kvpi(
            self.df_kvpi_evolution.columns, self.df_kvpi_evolution.columns[0]
        )
        self.create_year_sliders()
        self.update_kvpi_chart()

        self.main_layout.addWidget(self.category_cb_kvpi)
        self.main_layout.addLayout(self.slider_layout)
        self.main_layout.addWidget(self.kvpi_chart_canvas)

    def create_year_sliders(self):
        self.slider_layout = QtGui.QGridLayout()
        self.year_slider_kvpi_min = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.year_slider_kvpi_min.setMinimum(self.df_kvpi_evolution.index[0])
        self.year_slider_kvpi_min.setMaximum(self.df_kvpi_evolution.index[-1])
        self.year_slider_kvpi_min.setValue(self.df_kvpi_evolution.index[0])
        self.year_slider_kvpi_min.setTickPosition(QtGui.QSlider.TicksBelow)
        self.year_slider_kvpi_min.setTickInterval(1)
        self.min_year_label = QtGui.QLabel(str(self.year_slider_kvpi_min.value()), self)
        self.year_slider_kvpi_max = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.year_slider_kvpi_max.setMinimum(self.df_kvpi_evolution.index[0])
        self.year_slider_kvpi_max.setMaximum(self.df_kvpi_evolution.index[-1])
        self.year_slider_kvpi_max.setValue(self.df_kvpi_evolution.index[-1])
        self.year_slider_kvpi_max.setTickPosition(QtGui.QSlider.TicksBelow)
        self.year_slider_kvpi_max.setTickInterval(1)
        self.max_year_label = QtGui.QLabel(str(self.year_slider_kvpi_max.value()), self)
        self.year_slider_kvpi_min.valueChanged.connect(self.update_kvpi_chart)
        self.year_slider_kvpi_min.valueChanged.connect(self.update_min_year_label)
        self.year_slider_kvpi_max.valueChanged.connect(self.update_kvpi_chart)
        self.year_slider_kvpi_max.valueChanged.connect(self.update_max_year_label)
        self.slider_layout.addWidget(self.year_slider_kvpi_min, 1, 1)
        self.slider_layout.addWidget(self.min_year_label, 1, 2)
        self.slider_layout.addWidget(self.year_slider_kvpi_max, 2, 1)
        self.slider_layout.addWidget(self.max_year_label, 2, 2)

    def update_min_year_label(self, value):
        self.min_year_label.setText(str(value))

    def update_max_year_label(self, value):
        self.max_year_label.setText(str(value))

    def update_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.translate_kvpi_df()
            logger.info("Updating language KVPI")

    def translate_kvpi_df(self):
        selected_language = self.current_language
        self.translated_index = translate_labels(
            self.df_kvpi_evolution.columns.values.tolist(), language=selected_language
        )
        self.update_category_combobox_kvpi()

    def update_category_combobox_kvpi(self):
        current_index = self.category_cb_kvpi.currentIndex()
        self.category_cb_kvpi.clear()
        self.category_cb_kvpi.addItems(self.translated_index)
        self.category_cb_kvpi.setCurrentText(self.translated_index[current_index])

    def create_category_combobox_kvpi(self, cb_list, current_text):
        self.category_cb_kvpi = QtGui.QComboBox()
        self.category_cb_kvpi.addItems(cb_list)
        self.category_cb_kvpi.currentTextChanged.connect(self.update_kvpi_chart)
        self.category_cb_kvpi.setCurrentText(current_text)

    def update_kvpi_chart(self):
        selected_category = self.category_cb_kvpi.currentText()
        if selected_category != "":
            idx = self.translated_index.index(selected_category)
            idx_min = self.df_kvpi_evolution.index.get_loc(
                self.year_slider_kvpi_min.value()
            )
            idx_max = self.df_kvpi_evolution.index.get_loc(
                self.year_slider_kvpi_max.value()
            )
            x = self.df_kvpi_evolution.index[idx_min : idx_max + 1]
            y = self.df_kvpi_evolution.iloc[idx_min : idx_max + 1, idx].values
            self.kvpi_chart_canvas.axes.cla()
            self.kvpi_chart_canvas.axes.plot(x, y, label=selected_category)
            self.kvpi_chart_canvas.axes.set_xticks(x, rotation=45)
            self.kvpi_chart_canvas.axes.set_xticklabels(
                self.kvpi_chart_canvas.axes.get_xticks(), rotation=80
            )
            self.kvpi_chart_canvas.axes.grid()
            self.kvpi_chart_canvas.draw()


class LIK(QtGui.QTabWidget):
    def __init__(
        self,
        source_lik_weights="",
        source_lik_evolution="",
        current_language="",
    ):
        super().__init__()
        self.color_dict_lik = create_color_dict()
        self.setGeometry(100, 10, 900, 1200)
        self.lik_weights = LIKWeights(
            source_lik_weights, current_language, self.color_dict_lik
        )
        self.lik_evolution = LIKEvolution(
            source_lik_evolution, current_language, self.color_dict_lik
        )
        self.addTab(self.lik_evolution, "Evolution")
        self.addTab(self.lik_weights, "Weights")

    def upload_lik_colors_to_mysql(
        self, credentials, table_name="lik_colors", language="English"
    ):
        color_dict_rgb_javascript = create_RGB_dict_javascript(self.color_dict_lik)
        translated_labels = translate_labels(
            list(color_dict_rgb_javascript.keys()), language=language
        )
        self.db_interface = DBInterface(credentials=credentials)
        df = pd.DataFrame(color_dict_rgb_javascript, index=[0])
        df.columns = translated_labels
        type_dict = self.db_interface.infer_sqlalchemy_datatypes(df)
        logger.info(
            "Uploading data to SQL table %s in db %s",
            table_name,
            credentials["db_name"],
        )
        df.to_sql(
            table_name,
            con=self.db_interface.conn,
            if_exists="append",
            chunksize=1000,
            dtype=type_dict,
            index_label="id",
        )


class LIKEvolution(QtGui.QWidget):
    def __init__(self, lik_evolution_source, current_language, color_dict_lik):
        QtGui.QWidget.__init__(self)
        self.color_dict_lik = color_dict_lik
        self.current_language = current_language
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.get_lik_evolution_data(lik_evolution_source)
        self.evolution_chart_canvas = MplCanvas(self, width=5, height=6, dpi=100)
        self.create_category_combobox_evolution(
            self.df_lik_evolution.index, self.df_lik_evolution.index[0]
        )
        self.update_evolution_chart()

        self.main_layout.addWidget(self.category_cb_evolution)
        self.main_layout.addWidget(self.evolution_chart_canvas)

    def update_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.translate_lik_evolution_df()
            logger.info("Updating language")

    def translate_lik_evolution_df(self):
        selected_language = self.current_language
        self.translated_index = translate_labels(
            self.df_lik_evolution.index.values.tolist(), language=selected_language
        )
        self.update_category_combobox_evolution()

    def update_category_combobox_evolution(self):
        current_index = self.category_cb_evolution.currentIndex()
        self.category_cb_evolution.clear()
        self.category_cb_evolution.addItems(self.translated_index)
        self.category_cb_evolution.setCurrentText(self.translated_index[current_index])

    def get_lik_evolution_data(self, source_file):
        logger.info("Loading %s...", source_file)
        df_raw = pd.read_excel(source_file)
        category_names = [name.lstrip() for name in df_raw.iloc[422:434, 5]]
        end_of_month_list = [
            get_last_date_of_month(x.year, x.month) for x in df_raw.iloc[2, 14:]
        ]
        self.df_lik_evolution = pd.DataFrame(
            index=category_names,
            columns=end_of_month_list,
            data=df_raw.iloc[422:434, 14:].values,
            dtype="float64",
        )
        self.translated_index = self.df_lik_evolution.index.values.tolist()

    def create_category_combobox_evolution(self, cb_list, current_text):
        self.category_cb_evolution = QtGui.QComboBox()
        self.category_cb_evolution.addItems(cb_list)
        self.category_cb_evolution.currentTextChanged.connect(
            self.update_evolution_chart
        )
        self.category_cb_evolution.setCurrentText(current_text)

    def update_evolution_chart(self):
        selected_category = self.category_cb_evolution.currentText()
        if selected_category != "":
            idx = self.translated_index.index(selected_category)
            color = self.color_dict_lik[self.df_lik_evolution.index[idx]]
            x = self.df_lik_evolution.columns
            y = self.df_lik_evolution.iloc[idx].values
            self.evolution_chart_canvas.axes.cla()
            self.evolution_chart_canvas.axes.plot(
                x, y, color=color, label=selected_category
            )
            # self.evolution_chart_canvas.axes.set_xticks(x, rotation=45)
            # self.evolution_chart_canvas.axes.set_xticklabels(
            #     self.evolution_chart_canvas.axes.get_xticks(), rotation=80
            # )
            self.evolution_chart_canvas.axes.grid()
            self.evolution_chart_canvas.draw()

    def create_sql_table(
        self, credentials, table_name="lik_evolution", language="English"
    ):
        translated_labels = translate_labels(
            self.df_lik_evolution.index.values.tolist(), language=language
        )
        self.db_interface = DBInterface(credentials=credentials)

        df = self.df_lik_evolution.transpose()
        df.columns = translated_labels
        df.reset_index(names="Date", inplace=True)
        df["Date"] = df["Date"].map(lambda x: x.date()).astype("datetime64[ns]")
        type_dict = self.db_interface.infer_sqlalchemy_datatypes(df)
        df = pd.DataFrame(columns=df.columns)
        logger.info(
            "Creating SQL table %s in db %s", table_name, credentials["db_name"]
        )
        df.to_sql(
            table_name,
            con=self.db_interface.conn,
            if_exists="fail",
            chunksize=1000,
            dtype=type_dict,
            index_label="id",
        )

    def upload_data_to_sql_table(
        self, credentials, table_name="lik_evolution", language="English"
    ):
        translated_labels = translate_labels(
            self.df_lik_evolution.index.values.tolist(), language=language
        )
        self.db_interface = DBInterface(credentials=credentials)
        df = self.df_lik_evolution.transpose()
        df.columns = translated_labels
        df.reset_index(names="Date", inplace=True)
        df["Date"] = df["Date"].map(lambda x: x.date()).astype("datetime64[ns]")
        type_dict = self.db_interface.infer_sqlalchemy_datatypes(df)
        logger.info(
            "Uploading data to SQL table %s in db %s",
            table_name,
            credentials["db_name"],
        )
        df.to_sql(
            table_name,
            con=self.db_interface.conn,
            if_exists="append",
            chunksize=1000,
            dtype=type_dict,
            index_label="id",
        )


class LIKWeights(QtGui.QWidget):
    def __init__(self, lik_weight_source, current_language, color_dict_lik):
        QtGui.QWidget.__init__(self)
        self.color_dict_lik = color_dict_lik
        self.main_layout = QtGui.QVBoxLayout()

        self.setLayout(self.main_layout)
        self.main_dict = dict()
        self.main_dict["LIK2020"] = self.get_lik_weight_data(
            lik_weight_source, "LIK2020"
        )
        self.main_dict["LIK2015"] = self.get_lik_weight_data(
            lik_weight_source, "LIK2015"
        )
        self.main_dict["LIK2010"] = self.get_lik_weight_data(
            lik_weight_source,
            "LIK2010",
            index_col=3,
            start_row=4,
            column_row=2,
            level_col="Pos",
        )
        self.main_dict["LIK2005"] = self.get_lik_weight_data(
            lik_weight_source,
            "LIK2005",
            index_col=3,
            start_row=4,
            column_row=2,
            level_col="Pos",
        )
        self.main_dict["LIK2000"] = self.get_lik_weight_data(
            lik_weight_source,
            "LIK2000",
            index_col=2,
            start_row=4,
            column_row=2,
            level_col="Nr. ",
            create_level_col=True,
        )
        self.create_lik_dict()
        self.create_pie_chart_colors()
        current_year = "2022"  # str(datetime.datetime.now().year)
        self.current_language = current_language
        self.pie_chart_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.category_chart_canvas = MplCanvas(self, width=5, height=6, dpi=100)
        self.create_year_combobox(
            sorted(self.lik_dict.keys(), reverse=True), current_year
        )
        self.update_pie_chart()
        self.create_category_combobox(self.translated_index, self.translated_index[0])
        self.update_category_chart()
        self.top_layout = QtGui.QFormLayout()
        self.top_layout.addRow("Year", self.year_cb)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.pie_chart_canvas)
        self.bottom_layout = QtGui.QFormLayout()
        self.bottom_layout.addRow("Category", self.category_cb)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.addWidget(self.category_chart_canvas)

    def update_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.translate_lik_df()
            self.update_pie_chart()

    def create_year_combobox(self, cb_list, current_text):
        self.year_cb = QtGui.QComboBox()
        self.year_cb.addItems(cb_list)
        self.year_cb.currentTextChanged.connect(self.update_pie_chart)
        self.year_cb.setCurrentText(current_text)

    def create_category_combobox(self, cb_list, current_text):
        self.category_cb = QtGui.QComboBox()
        self.category_cb.addItems(cb_list)
        self.category_cb.currentTextChanged.connect(self.update_category_chart)
        self.category_cb.setCurrentText(current_text)

    def translate_lik_df(self):
        selected_language = self.current_language
        self.translated_index = translate_labels(
            self.lik_df.index.values.tolist(), language=selected_language
        )
        self.update_category_combobox()

    def update_category_combobox(self):
        current_index = self.category_cb.currentIndex()
        self.category_cb.clear()
        self.category_cb.addItems(self.translated_index)
        self.category_cb.setCurrentText(self.translated_index[current_index])

    def update_category_chart(self):
        selected_category = self.category_cb.currentText()
        if selected_category != "":
            idx = self.translated_index.index(selected_category)
            # current_index = self.category_cb.currentIndex()
            color = self.color_dict_lik[self.lik_df.index[idx]]
            # color = self.pie_chart_colors[current_index]
            x = self.lik_df.iloc[idx].index
            y = self.lik_df.iloc[idx].values
            self.category_chart_canvas.axes.cla()
            self.category_chart_canvas.axes.plot(
                x, y, color=color, label=selected_category
            )
            self.category_chart_canvas.axes.set_xticks(x, rotation=45)
            self.category_chart_canvas.axes.set_xticklabels(
                self.category_chart_canvas.axes.get_xticks(), rotation=80
            )
            self.category_chart_canvas.axes.set_xlabel("Year")
            self.category_chart_canvas.axes.set_ylabel("%")
            self.category_chart_canvas.axes.legend()
            self.category_chart_canvas.axes.grid()
            self.category_chart_canvas.draw()

    def create_pie_chart_colors(self):
        self.pie_chart_colors = [
            self.color_dict_lik[category] for category in self.lik_df.index
        ]

    def update_pie_chart(self):
        selected_year = str(self.year_cb.currentText())
        selected_language = self.current_language
        self.current_pie_data = self.lik_dict[selected_year]
        self.pie_chart_canvas.axes.cla()
        sizes = self.current_pie_data.values
        labels = self.current_pie_data.index.values.tolist()
        labels_translated = translate_labels(labels, language=selected_language)
        self.pie_chart_canvas.axes.pie(
            sizes,
            labels=labels_translated,
            autopct="%1.1f%%",
            shadow=False,
            startangle=90,
            counterclock=False,
            colors=self.pie_chart_colors,
        )
        self.pie_chart_canvas.axes.set_title("LIK Weights")
        self.pie_chart_canvas.axes.axis("equal")
        self.pie_chart_canvas.draw()

    def get_weights(self, df, level, year):
        weights = df[df["Level"] == level].loc[:, year]
        return weights

    def create_lik_dict(self, level=2):
        self.lik_dict = dict()
        self.lik_df = pd.DataFrame()
        current_year = datetime.datetime.now().year
        for df in self.main_dict.values():
            years = [x for x in df.columns if type(x) is not str]
            for year in years:
                if year <= current_year:
                    self.lik_dict[str(int(year))] = df[df["Level"] == level].loc[
                        :, year
                    ]
                    self.lik_df.loc[:, int(year)] = df[df["Level"] == level].loc[
                        :, year
                    ]
        self.lik_df = self.lik_df[self.lik_df.columns.sort_values()]
        self.translated_index = self.lik_df.index.values.tolist()

    def get_lik_weight_data(
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
            df = df.rename(columns={"2000/01": 2000})
            df.loc[:, 2001] = df.loc[:, 2000]
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
    def store_var_to_json(variable_to_store, file_name):
        with open(file_name, "w") as file:
            json.dump(variable_to_store, file, indent=4)

    def store_weights_to_json(self, language="English"):
        self.language_cb.setCurrentText(language)
        self.translate_lik_df()
        target_dir = "lik_json_files"
        filepath = Path.cwd() / target_dir
        filepath.mkdir(parents=True, exist_ok=True)
        for year in self.lik_df.columns:
            dict_to_store = {
                "labels": self.lik_df.loc[:, year].index.values.tolist(),
                "datasets": [{"data": self.lik_df.loc[:, year].values.tolist()}],
            }
            self.store_var_to_json(
                dict_to_store, target_dir + "/" + "weights_" + str(year) + ".json"
            )

    def store_color_to_json(self):
        color_string_list = []
        target_dir = "lik_json_files"
        filepath = Path.cwd() / target_dir
        filepath.mkdir(parents=True, exist_ok=True)
        for color in self.pie_chart_colors:
            color_string_list.append(
                "rgb("
                + str(floor(255 * color[0]))
                + ","
                + str(floor(255 * color[1]))
                + ","
                + str(floor(255 * color[2]))
                + ")"
            )
        pie_chart_color_dict = {"pie_chart_colors": color_string_list}
        self.store_var_to_json(
            pie_chart_color_dict, target_dir + "/" + "pie_chart_color.json"
        )

    def store_categories_to_json(self):
        category_list = []
        target_dir = "lik_json_files/category_lik"
        filepath = Path.cwd() / target_dir
        filepath.mkdir(parents=True, exist_ok=True)
        years = self.lik_df.columns.values.tolist()
        evolution_dict = {"labels": years, "datasets": [{"label": "N/A", "data": []}]}
        for category in self.lik_df.index:
            abbreviation = category.replace(" ", "_")
            evolution_dict["datasets"][0]["label"] = category
            evolution_dict["datasets"][0]["data"] = self.lik_df.loc[
                category, :
            ].values.tolist()
            self.store_var_to_json(
                evolution_dict, target_dir + "/" + abbreviation + ".json"
            )
            category_list.append({"name": category, "abbreviation": abbreviation})
        self.store_var_to_json(category_list, target_dir + "/" + "categories.json")

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
    def __init__(
        self,
        parent=None,
        source_lik_weights="",
        source_lik_evolution="",
        source_kvpi_evolution="",
        current_language="",
    ):
        super(InflationTracker, self).__init__(parent)
        self.setGeometry(100, 10, 900, 1200)
        self.lik = LIK(source_lik_weights, source_lik_evolution, current_language)
        self.kvpi = KVPI(source_kvpi_evolution, current_language)
        self.addTab(self.lik, "LIK")
        self.addTab(self.kvpi, "KVPI")
        self.setCurrentIndex(1)

    def store_data_to_json(self):
        self.lik.store_weights_to_json()
        self.lik.store_color_to_json()
        self.lik.store_categories_to_json()

    def create_sql_tables(self, credentials):
        self.lik.lik_evolution.create_sql_table(credentials)

    def upload_data_to_sql_tables(self, credentials):
        self.lik.lik_evolution.upload_data_to_sql_table(credentials)


class MainWindow(QtGui.QMainWindow):
    """Main Window."""

    language_changed = QtCore.pyqtSignal(str)

    def __init__(
        self, source_lik_weights="", source_lik_evolution="", source_kvpi_evolution=""
    ):
        super().__init__()

        self.current_language = "German"
        self.inflation_tracker = InflationTracker(
            source_lik_weights=source_lik_weights,
            source_lik_evolution=source_lik_evolution,
            source_kvpi_evolution=source_kvpi_evolution,
            current_language=self.current_language,
        )
        self.language_changed.connect(self._update_language)

        self.setWindowTitle("Inflation tracker")
        self.setGeometry(100, 10, 950, 1250)
        self.setCentralWidget(self.inflation_tracker)
        self._create_menu_bar()

    def _update_language(self, language):
        self.inflation_tracker.lik.lik_weights.update_language(language)
        self.inflation_tracker.lik.lik_evolution.update_language(language)
        self.inflation_tracker.kvpi.kvpi_evolution.update_language(language)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        language_menu = QtGui.QMenu("&Language", self)
        select_language_menu = language_menu.addMenu("&Select")
        self.select_english_action = QtGui.QAction("English", self)
        self.select_english_action.setCheckable(True)
        self.select_english_action.setChecked(False)
        self.select_english_action.triggered.connect(self._create_to_english)
        self.select_german_action = QtGui.QAction("German", self)
        self.select_german_action.setCheckable(True)
        self.select_german_action.setChecked(True)
        self.select_german_action.triggered.connect(self._change_to_german)
        select_language_menu.addAction(self.select_english_action)
        select_language_menu.addAction(self.select_german_action)
        menu_bar.addMenu(language_menu)

    def _create_to_english(self):
        if self.current_language != "English":
            self.current_language = "English"
            logger.info("Change current language to English")
            self.language_changed.emit(self.current_language)
            self.select_german_action.setChecked(False)
            self.select_english_action.setChecked(True)

    def _change_to_german(self):
        if self.current_language != "German":
            self.current_language = "German"
            logger.info("Change current language to German")
            self.language_changed.emit(self.current_language)
            self.select_german_action.setChecked(True)
            self.select_english_action.setChecked(False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lik_weights",
        help="xlsx file containing LIK weights",
        default="data/lik_weights.xlsx",  # ToDo: Automate download of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/erhebungen/lik/warenkorb.assetdetail.21484892.html
    )
    parser.add_argument(
        "--lik_evolution",
        help="xlsx file containing LIK evolution over time",
        default="data/lik_evolution.xlsx",  # ToDo: Automate download of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/landesindex-konsumentenpreise/detailresultate.assetdetail.23925501.html
    )
    parser.add_argument(
        "--kvpi_evolution",
        help="xlsx file containing KVPI evolution over time",
        default="data/kvpi_index.xlsx",  # ToDo: Automate download of .xlsx file from https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/krankenversicherungspraemien.assetdetail.23749019.html
    )

    parser.add_argument(
        "--json",
        help="If selected the data will not be visualized but it will store all the relevant tax rates in .json files",
        action="store_true",
    )
    parser.add_argument(
        "--create_sql_table",
        help="If selected new empty table is created with given name",
        action="store_true",
    )
    parser.add_argument(
        "--upload_to_sql",
        help="If selected, uploads the data to a SQL database",
        action="store_true",
    )
    parser.add_argument(
        "--create_lik_color_sql_table",
        help="If selected, creates sql table containing the javascript colorscodes",
        action="store_true",
    )
    parser.add_argument(
        "--credentials_file",
        help="Path to .json file containing db credentials",
        default="",
    )

    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)
    setup_translation()
    credentials_sql = {
        "hostname": "127.0.0.1",
        "user": "root",
        "password": "",
        "db_name": "dummy",
        "port": "3306",
    }
    if args.credentials_file != "":
        credentials_sql = DBInterface.load_db_credentials(args.credentials_file)

    main_window = MainWindow(
        source_lik_weights=args.lik_weights,
        source_lik_evolution=args.lik_evolution,
        source_kvpi_evolution=args.kvpi_evolution,
    )
    if (
        not args.json
        and not args.create_sql_table
        and not args.upload_to_sql
        and not args.create_lik_color_sql_table
    ):
        main_window.show()
        sys.exit(app.exec_())
    if args.create_sql_table:
        main_window.inflation_tracker.create_sql_tables(credentials_sql)
    if args.upload_to_sql:
        main_window.inflation_tracker.upload_data_to_sql_tables(credentials_sql)
    if args.json:
        main_window.inflation_tracker.store_data_to_json()
    if args.create_lik_color_sql_table:
        main_window.inflation_tracker.lik.upload_lik_colors_to_mysql(credentials_sql)


if __name__ == "__main__":
    main()
# Next: Viszualize inflation evolvment directly from SQL database e.g. MYSQL. Tutorial here https://dyclassroom.com/chartjs/chartjs-how-to-draw-bar-graph-using-data-from-mysql-table-and-php
# Next: Install XAMPP according to https://undsgn.com/xampp-tutorial/
# Next: make comparison which category grew the most https://www.bfs.admin.ch/bfs/de/home/statistiken/preise/landesindex-konsumentenpreise/detailresultate.assetdetail.23344559.html
# Next: Make second plot with first level of subcategories. Especially considering health costs very interesting graph. -> Could also be then the post after the next
