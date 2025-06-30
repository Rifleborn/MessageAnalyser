from telethon import TelegramClient

async def loadSpecificDialog(self, client, dialogTitle, loadFromClient):
    try:
        if not await client.is_user_authorized():
            print(f"[ERROR] Client is not authorized")
        else:
            print(f"[DEBUG] Loading dialogs...")

        # show messages only from specific client
        if loadFromClient:
            clientId = (await client.get_me()).id
            async for message in client.iter_messages(dialogTitle, offset_date=self.endDate, reverse=True):
                if message.sender_id == clientId:
                    print(f"[{message.date.strftime('%Y-%m-%d %H:%M')}] {message.sender_id}: \n{message.text}\n")
    except Exception as e:
        print(f"[ERROR] Unexpected error in dialogLoader, loadSpecificDialog()")
