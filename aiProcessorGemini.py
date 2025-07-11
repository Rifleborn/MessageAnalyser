import json
import os
import re
from datetime import datetime

from google import genai
from google.genai import types

def extractAnswer(responseText):

    validAnswers = {"Так", "Ні", "В процесі", "-"}

    matches = re.findall(r'\*\*(.*?)\*\*', responseText)

    for match in matches:
        resp1 = match.strip()
        if resp1 in validAnswers:
            return resp1

    for resp2 in validAnswers:
        if resp2 in responseText:
            return resp2

    return None

def processDialog(self, dialogsToProcess):
    dialogsToProcess = [
        # 1. Менеджер пообіцяв і не відповів — вчора
        {
            'chat_name': 'СТО Клієнт 1',
            'manager': 'Ігор',
            'messages': [
                {'from': 'client1', 'is_from_manager': False, 'date': '11:00 01-07-2025',
                 'text': 'Скільки буде коштувати ремонт підвіски?'},
                {'from': 'igor_manager', 'is_from_manager': True, 'date': '11:15 01-07-2025',
                 'text': 'Зроблю прорахунок до кінця дня'},
            ],
            'lastdate': '11:15 01-07-2025'
        },
        # 2. Менеджер пообіцяв і відповів
        {
            'chat_name': 'СТО Клієнт 2',
            'manager': 'Олена',
            'messages': [
                {'from': 'client2', 'is_from_manager': False, 'date': '10:00 25-06-2025',
                 'text': 'Потрібен прорахунок на заміну гальм'},
                {'from': 'olena_manager', 'is_from_manager': True, 'date': '10:20 25-06-2025',
                 'text': 'Скину до кінця дня'},
                {'from': 'olena_manager', 'is_from_manager': True, 'date': '18:00 25-06-2025',
                 'text': 'Орієнтовно 3800 грн з роботою'},
            ],
            'lastdate': '18:00 25-06-2025'
        },
        # 3. Обіцянка, але не відповів уже 5 днів
        {
            'chat_name': 'СТО Клієнт 3',
            'manager': 'Максим',
            'messages': [
                {'from': 'client3', 'is_from_manager': False, 'date': '09:00 27-06-2025',
                 'text': 'Чекаю на обрахунок по зчепленню'},
                {'from': 'max_manager', 'is_from_manager': True, 'date': '09:15 27-06-2025',
                 'text': 'До вечора надішлю'},
            ],
            'lastdate': '09:15 27-06-2025'
        },
        # 4. Не обіцяв нічого — має бути "-"
        {
            'chat_name': 'СТО Клієнт 4',
            'manager': 'Анна',
            'messages': [
                {'from': 'client4', 'is_from_manager': False, 'date': '13:00 28-06-2025',
                 'text': 'Коли буде готове авто?'},
                {'from': 'anna_manager', 'is_from_manager': True, 'date': '13:10 28-06-2025',
                 'text': 'До завтра має бути готове'},
            ],
            'lastdate': '13:10 28-06-2025'
        },
        # 5. Менеджер відповів наступного дня — запізно
        {
            'chat_name': 'СТО Клієнт 5',
            'manager': 'Петро',
            'messages': [
                {'from': 'client5', 'is_from_manager': False, 'date': '15:00 20-06-2025',
                 'text': 'Скільки коштує заміна радіатора?'},
                {'from': 'petro_manager', 'is_from_manager': True, 'date': '15:30 20-06-2025',
                 'text': 'Скажу до вечора'},
                {'from': 'petro_manager', 'is_from_manager': True, 'date': '10:00 21-06-2025',
                 'text': 'Ціна близько 3200 грн'},
            ],
            'lastdate': '10:00 21-06-2025'
        },
        # 6. Клієнт просить прорахунок — менеджер ще не відповів (сьогодні)
        {
            'chat_name': 'СТО Клієнт 6',
            'manager': 'Світлана',
            'messages': [
                {'from': 'client6', 'is_from_manager': False, 'date': '09:30 02-07-2025',
                 'text': 'Можете зробити прорахунок по кондиціонеру?'},
            ],
            'lastdate': '09:30 02-07-2025'
        },
        # 7. Обіцянка виконана
        {
            'chat_name': 'СТО Клієнт 7',
            'manager': 'Ірина',
            'messages': [
                {'from': 'client7', 'is_from_manager': False, 'date': '16:00 18-06-2025',
                 'text': 'Потрібен прорахунок по покрасці'},
                {'from': 'iryna_manager', 'is_from_manager': True, 'date': '16:10 18-06-2025',
                 'text': 'Скину до кінця дня'},
                {'from': 'iryna_manager', 'is_from_manager': True, 'date': '19:00 18-06-2025', 'text': 'Ціна 5500 грн'},
            ],
            'lastdate': '19:00 18-06-2025'
        },
        # 8. В процесі — обіцянка сьогодні
        {
            'chat_name': 'СТО Клієнт 8',
            'manager': 'Юрій',
            'messages': [
                {'from': 'client8', 'is_from_manager': False, 'date': '10:00 02-07-2025',
                 'text': 'Розрахуйте, будь ласка, ремонт коробки передач'},
                {'from': 'yuriy_manager', 'is_from_manager': True, 'date': '10:30 02-07-2025',
                 'text': 'Ок, зроблю до вечора'},
            ],
            'lastdate': '10:30 02-07-2025'
        },
        # 9. Без теми прорахунку
        {
            'chat_name': 'СТО Клієнт 9',
            'manager': 'Тарас',
            'messages': [
                {'from': 'client9', 'is_from_manager': False, 'date': '11:00 19-06-2025',
                 'text': 'Можна записатись на ТО?'},
                {'from': 'taras_manager', 'is_from_manager': True, 'date': '11:10 19-06-2025',
                 'text': 'Так, на понеділок зручно?'},
            ],
            'lastdate': '11:10 19-06-2025'
        },
        # 10. Обіцяв і ще не відповів — прострочено
        {
            'chat_name': 'СТО Клієнт 10',
            'manager': 'Леся',
            'messages': [
                {'from': 'client10', 'is_from_manager': False, 'date': '08:00 29-06-2025',
                 'text': 'Що по прорахунку кузовного ремонту?'},
                {'from': 'lesya_manager', 'is_from_manager': True, 'date': '08:15 29-06-2025',
                 'text': 'До вечора все скину'},
            ],
            'lastdate': '08:15 29-06-2025'
        },
    ]


    try:
        if len(dialogsToProcess) != 0:

            # api-key from file
            with open("credentials/gemini_key.txt", "r") as f:
                api_key = f.read().strip()

            os.environ["GEMINI_API_KEY"] = api_key

            # The client gets the API key from the environment variable `GEMINI_API_KEY`.
            client = genai.Client()
            currentDatetime = datetime.now()

            for dialog in dialogsToProcess:
                 print(f'[DEBUG] Processing dialog, manager: {dialog["manager"]}')

                 try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction="Ти аналітик, що аналізує діалоги між клієнтом і менеджером."),
                        contents=f"Ось діалог: {json.dumps(dialog['messages'])}.\n"
                                 f"Визнач, чи пообіцяв менеджер надіслати обрахунок клієнту (грошова сума, наприклад, '5400' або '28300 грн.'), та чи виконав обіцянку\n"
                                 f"Поточна системна дата та час: {currentDatetime}.\n"
                                 f"Надішли 'Так', якщо менеджер надіслав повідомлення з обрахунком, і це повідомлення було надіслане до вказаної дати обіцянки (або включно з нею)."
                                 f"Надішли 'Ні', якщо менеджер пообіцяв надіслати обрахунок до певної дати/часу (наприклад, 'до кінця дня X числа'), а поточна дата/час вже минула цю обіцяну дату/час, і повідомлення з обрахунком відсутнє"
                                 f"Надішли 'В процесі', якщо менеджер пообіцяв надіслати обрахунок до певної дати/часу (наприклад, 'до кінця дня X числа'), і поточна дата/час ще не минула цю обіцяну дату/час, і повідомлення з обрахунком відсутнє."
                                 f"Надішли '-', якщо у діалозі мова про розрахунок/обрахунок не велася"
                                 f"Для визначення 'поточного дня' та часу використовувати актуальну системну дату та час"
                                 f"Якщо обіцянка 'до кінця дня', це означає до 23:59:59 вказаного дня."

                    )

                    print(f'[DEBUG] Gemini response: {response.text}')
                    resp = extractAnswer(response.text)
                    # Так, Ні, В процесі, -
                    if (resp != '-' and (resp == 'Так' or resp == 'Ні' or resp == 'В процесі')):
                        addList = (dialog["lastdate"], dialog["chat_name"], dialog["manager"], resp)
                        print(addList)
                        self.mainTable.add_row(addList)
                    else:
                        print(f'[DEBUG] Мова про розрахунок не велася з {dialog["chat_name"]}')

                 except Exception as e:
                     print(f'[ERROR] Unexpected error with AI response in aiProcessor.py, processDialog() : {e}')
                 # time.sleep(2)

        else:
            print(f'[ERROR] No dialogs to process')

    except Exception as e:
        print(f'[ERROR] Unexpected error in aiProcessor.py, processDialog() : {e}')

    try:
        self.tableSpinner.opacity = 0
    except AttributeError as e:
        print("[ERROR] UI component missing or not initialized:", e)
    except Exception as e:
        print("[ERROR] Unexpected error while updating UI state:", e)
