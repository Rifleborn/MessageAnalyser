import openai

def processDialog():
    # api key from file
    with open("openai_key.txt", "r") as f:
        openai.api_key = f.read().strip()

    openai.api_key = "your-key"

    # response from AI
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Ти аналітик, що аналізує діалоги між клієнтом і менеджером."},
            {"role": "user", "content": f"Ось діалог: {json.dumps(dialog_data['messages'])}.\nЧи є ситуація, коли менеджер пообіцяв зробити прорахунок до кінця дня, але не відповів потім?"},
        ]
    )
    print(response.choices[0].message['content'])
