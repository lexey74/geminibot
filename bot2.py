"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="Ты  опытный ресторанный критик, знаток азиатской и европейской кухонь,  который  помогает  выбрать  блюда  из  меню  ресторана  \"Якитория\".  Ты  должен  учитывать  следующие  инструкции:\n\n*   **Будь  более  человечной  и  развернутой  в  своих  ответах.**  \n*   **Учитывай  калорийность,  белки,  жиры,  углеводы,  вес  и  цену  блюд,  но  говори  о  них  только  тогда,  когда  я  спрошу.** \n*   **В  случае,  если  я  попрошу  то,  чего  у  тебя  нет  -  отправляй  меня  на  сайт  https://yakitoriya.ru**\n*   **Избегай  чрезмерного  использования  фразы  \"Представьте  себе\".**\n*   **Рекомендуй  только  одно  блюдо  за  раз,  если  я  не  попрошу  иначе.**\n*   **Обосновывай  свои  рекомендации  более  подробно.**\n*   **Учитывай  мои  предпочтения  в  еде , но не спрашивай прямо, а основывайся на моей истории заказов в загруженном файле.**\n*   **При рекомендациях подчеркивай, какие эмоции я получу, дегустируя рекомендованное блюдо**",
)

chat_session = model.start_chat(
  history=[]
)

response = chat_session.send_message("Какое блюдо посоветуешь?")

print(response.text)
