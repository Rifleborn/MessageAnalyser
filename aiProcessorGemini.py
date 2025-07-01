import json
import os

from google import genai
from google.genai import types

def processDialog(self, dialogsToProcess):
    try:
        if len(dialogsToProcess) != 0:

            # api-key from file
            with open("credentials/gemini_key.txt", "r") as f:
                api_key = f.read().strip()

            os.environ["GEMINI_API_KEY"] = api_key

            # The client gets the API key from the environment variable `GEMINI_API_KEY`.
            client = genai.Client()

            for dialog in dialogsToProcess:
                 print(f'[DEBUG] Processing dialog, manager: {dialog["manager"]}')

                 try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction="Ти аналітик, що аналізує діалоги між клієнтом і менеджером."),
                        contents=f"Ось діалог: {json.dumps(dialog['messages'])}.\nВизнач чи пообіцяв менеджер надіслати обрахунок клієнту, та чи виконав обіцянку."
                                 f"Надішли 'Так' якщо менеджер виконав обіцянку. Надішли 'Ні' якщо менеджер забув надіслати відповідне повідомлення клієнту. "
                                 f"Якщо наразі не відомо, що менеджер відповів пізніше або не виконав свою обіцянку то надішли 'В процесі'"
                    )

                    # Так, Ні, В процесі
                    print(f'[DEBUG] Gemini response: {response.text}')
                    addList = (dialog["lastdate"],dialog["chat_name"],dialog["manager"],response.text)

                    print(addList)

                    self.mainTable.add_row(addList)

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
