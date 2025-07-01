from openai import OpenAI
import json
import time

def processDialog(self, dialogsToProcess):
    try:
        if len(dialogsToProcess) != 0:

            # api-key from file
            with open("credentials/openaikey.txt", "r") as f:
                client = OpenAI(
                    api_key=f.read().strip(),
                )

            # print(f'[DEBUG] Key: {openai.api_key}')

            for dialog in dialogsToProcess:
                print(f'[DEBUG] Processing dialog: {dialog}')

                try:
                    # response from AI
                    response = client.responses.create(
                        model="gpt-3.5-turbo",
                        instructions="Ти аналітик, що аналізує діалоги між клієнтом і менеджером.",
                        input=f"Ось діалог: {json.dumps(dialog['messages'])}.\nВизнач чи пообіцяв менеджер надіслати обрахунок клієнту, та чи виконав обіцянку."
                              f"Надішли YES якщо менеджер виконав обіцянку. Надішли NO якщо менеджер забув надіслати відповідне повідомлення клієнту. "
                              f"Якщо наразі не відомо, що менеджер відповів пізніше або не виконав свою обіцянку то надішли DONTKNOW"
                    )

                    print(f'[DEBUG] AI response: {response.output_text}')
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
