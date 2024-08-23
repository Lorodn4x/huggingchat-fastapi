# HuggingChat FastAPI

This is an API interface for HuggingChat, built using FastAPI. The project implements an OpenAI-compatible API using [hugging-chat-api](https://github.com/Soulter/hugging-chat-api).

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Lorodn4x/huggingchat-fastapi.git
   cd huggingchat-fastapi
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # For Windows
   source venv/bin/activate  # For Unix or MacOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and fill it with your data.

5. Run the server:
   ```
   python api.py
   ```

## Usage

The API will be available at `http://localhost:8000`. Main endpoints:

- POST `/v1/chat/completions`: Send a chat request
- GET `/v1/models`: Get a list of available models

Detailed API documentation can be found at `http://localhost:8000/docs`.

### Usage example

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="xxxxxx")

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

## Important Note

This project uses [HuggingChat](https://huggingface.co/chat/) as its foundation. If HuggingFace requests the removal of this project, we will promptly comply with their request.

## License

This project is licensed under the [MIT License](LICENSE).

[Русская версия](README.md)
