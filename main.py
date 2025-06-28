import kivy
kivy.require('2.0.0')
# kivymd - 1.1.1

import logging
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

from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.spinner import MDSpinner

import asyncio
from threading import Thread

import json

from telethon import TelegramClient

loop = asyncio.new_event_loop()

# declare .kv file as class to access it
class MainWidget(Widget):
    pass

# loads .kv file with monitor### name
class Monitor(MDApp):

    def build(self):

        # variables
        self.loadMoreIsPressed = False
        self.totalRowsInSheet = 0
        self.totalRows = 0

        self.rootWidget = MainWidget()

        self.async_loop = asyncio.new_event_loop()
        Thread(target=self.startLoop, daemon=True).start()

        self.mainTable = MDDataTable(
            use_pagination=True,
            pos_hint = {'center_x': 0.5, 'center_y': 0.5},
            # check=True,
            column_data=[
                ("Час", dp(15)),
                ("Дата", dp(19)),
                ("Текст", dp(12)),
                ("Номер", dp(17)),
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

        button = MDRaisedButton(
            text="Завантажити",
            # size_hint=(1, 0.15),
            size_hint=(0.8, 0.1),
            pos_hint = {"center_x": 0.5},
            font_style="H5",  # Більший і жирний текст
            md_bg_color=(0.224, 0.800, 0.776, 1),
            on_release=self.loadButtonAction,
        )

        self.rootWidget.ids.footer.add_widget(button)

        with open("credentials/creds.json") as f:
            config = json.load(f)

        self.rootWidget.ids.idField.text = str(config['api_id'])
        self.rootWidget.ids.hashField.text = str(config['api_hash'])
        self.rootWidget.ids.phoneNumberField.text = str(config['phone_number'])

        return self.rootWidget

    def loadButtonAction(self, instance):
        asyncio.run_coroutine_threadsafe(self.loginToClient(), self.async_loop)

    async def loginToClient(self):
        print('[DEBUG] --Connecting to telegram--')

        try:
            client = TelegramClient('default_session', self.rootWidget.ids.idField.text, self.rootWidget.ids.hashField.text)
            phoneNumber = self.rootWidget.ids.phoneNumberField.text

            await client.connect()

            # check if client not authorized
            if not await client.is_user_authorized():

                # auth code
                try:
                    await client.send_code_request(phoneNumber)
                except Exception as e:
                    print(f"[ERROR] Unexpected error: {e}")
                    return

                verificationCode = input("Enter the code you received:")

                # 2fa
                try:
                    await client.sign_in(phoneNumber, verificationCode)
                except Exception as e:
                    print(f"[ERROR] Unexpected error: {e}")

                    twoFactorCode = input("[DEBUG] 2FA:")
                    await client.sign_in(password=twoFactorCode)

            # testing connection
            print(await client.get_me().stringify())
            await client.send_message('me', 'Hello to myself!')

        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

        finally:
            if 'client' in locals():
                client.disconnect()

    def startLoop(self):
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()

    def showError(self, message):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Error",
                text=message,
                buttons=[
                    MDFlatButton(
                        text="OK", on_release=lambda x: self.dialog.dismiss()
                    ),
                ],
            )
        self.dialog.text = message
        self.dialog.open()

# run application
if __name__ == '__main__':
    Monitor().run()