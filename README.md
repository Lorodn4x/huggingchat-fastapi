# HuggingChat FastAPI

Это API-интерфейс для HuggingChat, построенный с использованием FastAPI. Проект реализует API, совместимый с OpenAI, используя [hugging-chat-api](https://github.com/Soulter/hugging-chat-api).

## Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/Lorodn4x/huggingchat-fastapi.git
   cd huggingchat-fastapi
   ```

2. Создайте виртуальное окружение и активируйте его:
   ```
   python -m venv venv
   venv\Scripts\activate  # Для Windows
   source venv/bin/activate  # Для Unix или MacOS
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` на основе `.env.example` и заполните его вашими данными.

5. Запустите сервер:
   ```
   python api.py
   ```

## Использование

API будет доступен по адресу `http://localhost:8000`. Основные эндпоинты:

- POST `/v1/chat/completions`: Отправка запроса на чат
- GET `/v1/models`: Получение списка доступных моделей

Подробную документацию API можно найти по адресу `http://localhost:8000/docs`.

### Пример использования

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="xxxxxx")

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
    messages=[
        {"role": "user", "content": "Привет, как дела?"}
    ]
)

print(response.choices[0].message.content)
```

## Важное примечание

Этот проект использует [HuggingChat](https://huggingface.co/chat/) в качестве основы. Если HuggingFace попросит удалить этот проект, мы немедленно выполним их просьбу.

## Лицензия

Этот проект лицензирован под [MIT License](LICENSE).

[English version](README_EN.md)
