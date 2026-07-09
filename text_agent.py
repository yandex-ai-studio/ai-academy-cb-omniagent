import openai

YANDEX_CLOUD_MODEL = "yandexgpt"


class TextAgent:

    previous_id = None # Сохранение идентификатора последнего ответа

    def __init__(self, api_key: str, base_url: str, project: str):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            project=project
        )
        self.model = f"gpt://{project}/{YANDEX_CLOUD_MODEL}"
        
        pass
        

    def send(self, user_input: str) -> str:
        
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "Ты ассистент по подбору товаров и ответы на вопросы интернет-магазина Яндекс Маркет. "
                    "Твоя задача - помогать пользователям находить товары и отвечать на их вопросы. "
                    "Если требуется поиск в интернете, искать надо только на сайте market.yandex.ru. "
                    "Если найден подходящий товар, предоставь ссылки на сайт. "
                    "Отвечай четко и по делу, избегай лишних слов. "
                    "Если не знаешь точного ответа, честно скажи об этом." 
            ),
            tools=[
                {
                    "web_search": {
                        "filters": {
                            "allowed_domains": [
                                "market.yandex.ru"
                            ]
                        },
                        "user_location": {
                            # "region": "213", # Москва
                        }
                    }
                } 
                #,
                # {
                #     "type": "file_search",
                #     "vector_store_ids": ['<id_vector_store>']
                # }
            ],
            input=[{"role": "user", "content": user_input}],
            previous_response_id=self.previous_id  # Передача контекста, если он есть
        )

        # Сохранение идентификатора для следующего шага
        self.previous_id = response.id

        # Вывод ответа агента
        return response.output_text
