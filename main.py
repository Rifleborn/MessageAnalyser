import kivy
kivy.require('2.0.0')
# kivymd - 1.1.1
from gdataprocessor import loadGoogleData

import logging

import asyncio
from threading import Thread

# This modifies the console output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.getLogger("kivy").setLevel(logging.WARNING)
logging.getLogger("kivymd").setLevel(logging.WARNING)

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivymd.app import MDApp

# data table
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.spinner import MDSpinner

loop = asyncio.new_event_loop()

# declare .kv file as class to access it
class MainWidget(Widget):
    pass

# loads .kv file with monitor### name
class Monitor(MDApp):
    # Start asyncio event loop in background thread

    # second is optional button instance
    def loadMoreRecords(self, instance=None):
        if (self.loadMoreIsPressed == False):
            self.loadMoreIsPressed = True

            self.tableSpinner.opacity = 1
            self.tableSpinner.disabled = False

            asyncio.run_coroutine_threadsafe(loadGoogleData(self, 5), self.async_loop)

        else:
            print("[ARDUINO PROJECT] Error: button loadMore already pressed! Loading skipped.")

    def build(self):

        # variables
        self.loadMoreIsPressed = False
        self.totalRowsInSheet = 0
        self.totalRows = 0

        self.rootWidget = MainWidget()

        self.async_loop = asyncio.new_event_loop()
        Thread(target=self.start_loop, daemon=True).start()

        self.mainTable = MDDataTable(
            use_pagination=True,
            pos_hint = {'center_x': 0.5, 'center_y': 0.5},
            # check=True,
            column_data=[
                ("Час", dp(15)),
                ("Дата", dp(19)),
                ("Teмп.", dp(12)),
                ("Вологість", dp(17)),
                ("Повітря", dp(16)),
                ("Дощ", dp(21)),
            ],
            row_data=[],
            elevation=2,
        )

        self.rootWidget.ids.table_container.add_widget(self.mainTable)

        #  add it to spinner
        self.tableSpinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(46), dp(46)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            active=True
        )

        self.rootWidget.ids.table_container.add_widget(self.tableSpinner)

        button = MDRaisedButton(
            text="Завантажити ще",
            # size_hint=(1, 0.15),
            size_hint=(0.8, 0.1),
            pos_hint = {"center_x": 0.5},
            font_style="H5",  # Більший і жирний текст
            md_bg_color=(0.224, 0.800, 0.776, 1),
        )

        button.bind(on_release=self.loadMoreRecords)
        self.rootWidget.ids.footer.add_widget(button)

        self.loadMoreRecords()

        return self.rootWidget

    def start_loop(self):
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()

# run application
if __name__ == '__main__':
    Monitor().run()