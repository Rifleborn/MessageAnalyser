import kivy
kivy.require('2.0.0')
# kivymd - 1.1.1

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

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.getLogger("kivy").setLevel(logging.WARNING)
logging.getLogger("kivymd").setLevel(logging.WARNING)

import json
import asyncio
from threading import Thread
from telethon import TelegramClient
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# from aiProcessor import processDialog
from aiProcessorGemini import processDialog

DIALOGS_TO_LOAD = 10
loop = asyncio.new_event_loop()

# declare .kv file as class to access it
class MainWidget(Widget):
    pass

# loads .kv file with monitor### name
class MessageAnalyser(MDApp):

    # date range
    startDate = datetime.now()
    endDate = startDate - timedelta(30)

    # dialogs that will be processed by AI
    dialogsToProcess = []

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
                ("Дата останнього\n   повідомлення", dp(28)),
                ("Клієнт/чат", dp(22)),
                ("Менеджер", dp(22)),
                ("Клієнту\nвідповіли", dp(16)),
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

        buttonLogin = MDRaisedButton(
            text="Підключитися та \nзавантажити діалоги",
            size_hint=(1, 1),
            # pos_hint = {"center_x": 0.5},
            font_style="H6",
            md_bg_color=(0.224, 0.800, 0.776, 1),
            on_release=self.loginButtonAction,
        )

        self.rootWidget.ids.buttonContainer.add_widget(buttonLogin)

        # try
        with open("credentials/creds.json") as f:
            config = json.load(f)

        self.rootWidget.ids.idField.text = str(config['api_id'])
        self.rootWidget.ids.hashField.text = str(config['api_hash'])
        self.rootWidget.ids.phoneNumberField.text = str(config['phone_number'])

        return self.rootWidget

    def loginButtonAction(self, instance):
        asyncio.run_coroutine_threadsafe(self.loginToClient(), self.async_loop)

    async def loginToClient(self):
        print('[DEBUG] --Connecting to telegram--')

        try:
            self.rootWidget.ids.table_container.add_widget(self.tableSpinner)
        except Exception as e:
            print(f"[ERROR] Unexpected error in loginToClient(): {e}")

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
                    print(f"[ERROR] Unexpected error with request code: {e}")
                    return

                verificationCode = input("Enter the code you received:")

                # 2fa
                try:
                    await client.sign_in(phoneNumber, verificationCode)
                except Exception as e:
                    print(f"[ERROR] Unexpected error with signing in: {e}")

                    twoFactorCode = input("[DEBUG] 2FA:")
                    await client.sign_in(password=twoFactorCode)

            print(f"[DEBUG] Start date: {self.startDate} | EndDate: {self.endDate}")

            asyncio.run_coroutine_threadsafe(self.loadDialogsClient(client), self.async_loop)

        except Exception as e:
            print(f"[ERROR] Unexpected error in loginToClient(): {e}")

    async def loadDialogsClient(self, client):
        try:
            if not await client.is_user_authorized():
                print(f"[ERROR] Client is not authorized")
            else:
                print(f"[DEBUG] Loading dialogs...")

                # get first N dialogs
                dialogs = await client.get_dialogs(limit=DIALOGS_TO_LOAD)

                print(f"[DEBUG] Dialogs({len(dialogs)}) loaded:")

                for dialog in dialogs:
                    print(f"{dialog.name}", end=" ")
                print(f'\n')

                userInfo = await client.get_me()
                clientId = userInfo.id
                print(f'[DEBUG] Manager id: {clientId}\n')

                # print("=" * 40)

                for dialog in dialogs:
                    entity = dialog.entity

                    # set proper chat name depends on type of it: channel/user
                    if hasattr(entity, 'title'):
                       chatName = entity.title
                    elif entity.username:
                        chatName = entity.username
                    else:
                        chatName = entity.first_name

                    print(f"Чат/Отримувач: {chatName} | Повідомлення:\n")


                    specificDialog = {
                        # "chat_id": entity.id,
                        "chat_name": getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(
                            entity, 'username', None),
                        "manager": userInfo.first_name or userInfo.username,
                        "messages": []
                    }

                    # processing messages in chat
                    try:
                        # chat/dialog entity, oldest date, reverse
                        async for message in client.iter_messages(entity, offset_date=self.endDate, reverse=True):
                            sender = await message.get_sender()
                            local_time = message.date + timedelta(hours=3)  # UTC+3
                            msgDate = local_time.strftime('%H:%M %d-%m-%Y')

                            print(f"[{msgDate}] "
                                  f"{sender.first_name if sender.first_name else sender.username}:\n"
                                  f"{message.text}\n")

                            specificDialog["messages"].append({
                                "from": sender.username or sender.first_name,
                                "is_from_manager": (sender.id == clientId),
                                "date": str(msgDate),
                                "text": message.text,
                            })
                            # end of for

                        self.dialogsToProcess.append(specificDialog)
                        print(f"[DEBUG] Date of last message: {specificDialog['messages'][-1]['date']}")
                        specificDialog["lastdate"] = specificDialog['messages'][-1]['date']

                    except Exception as e:
                        print(f"[ERROR] Unexpected error when processing messages : {e}")


                    # separator for proper displaying dialogs in console
                    print("=" * 50)
                # end for

                print(f"[DEBUG] Dialogs to process:\n{self.dialogsToProcess}")

                # aiProcessor.py
                processDialog(self, self.dialogsToProcess)

        except Exception as e:
            print(f"[ERROR] Unexpected error in loadDialogsClient() : {e}")
        finally:
            self.tableSpinner.opacity = 0



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
    MessageAnalyser().run()