import os

import httpx
import openai
from dotenv import load_dotenv
from openai import APITimeoutError, APIError, OpenAI

load_dotenv()

# Для яндекса
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")

# Для Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROXY_URL = os.getenv("PROXY_URL")

http_client = httpx.Client(proxy=PROXY_URL) if PROXY_URL else None

if YANDEX_CLOUD_API_KEY and YANDEX_CLOUD_FOLDER :
    client_yandex = openai.OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url="https://ai.api.cloud.yandex.net/v1",
        project=YANDEX_CLOUD_FOLDER,
    )

if GEMINI_API_KEY :
    client_openAI = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        http_client=http_client
    )


model_yandexgpt_5_1 = "yandexgpt-5.1/latest"
model_gpt_oss_120b = "gpt-oss-120b/latest"
quen = "qwen3-235b-a22b-fp8/latest"

def call_yandex_gpt(prompt, system_instruction, temperature = 0.3, max_output_tokens= 3500, tools=None):
    if tools is None: tools = []

    try:
        response = client_yandex.responses.create(
            model=f"gpt://{YANDEX_CLOUD_FOLDER}/{model_yandexgpt_5_1}",
            temperature=temperature,
            instructions=system_instruction,
            input=prompt,
            max_output_tokens=max_output_tokens,
            timeout=600,
            tools=tools
        )

        if response.error is not None:
            raise Exception(response.error)

        return response.output_text

    except Exception as ex:
        print(f"[Yandex Error]: {ex}")
        raise

def call_gemini(prompt, system_instruction, temperature = 0.3, max_output_tokens= 3500, tools=None):
    if tools is None: tools = []

    try:
        response = client_openAI.chat.completions.create(
            model="gemini-3.1-pro-preview",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            timeout=600,
            max_tokens=max_output_tokens,
            tools=tools
        )

        return response.choices[0].message.content

    except Exception as ex:
        print(f"[Gemini Error]: {ex}")
        raise