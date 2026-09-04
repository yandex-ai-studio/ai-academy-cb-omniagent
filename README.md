# Текстовый и голосовой ассистент для сайта e-commerce или портала

## Введение

В этом примере демонстрируется, как развернуть приложение ассистента для работы с помощью текстового и голосового интерфейса с помощью сервисов AI Studio.

## Краткое описание задачи

Этот проект показывает, как создать и развернуть омни-агента, который работает в голосовом и текстовом режиме. Чтобы ответить пользователю, агент использует веб-поиск с ограничением по сайтам и поиск по внутренним документам. В примере для работы используется сервис Yandex AI Studio.

### Цель и ожидаемый результат

Поднимается бэкенд-приложение с единым интерфейсом к текстовой LLM и realtime-модели. На бэкенде размещается тестовая веб-страница для взаимодействия.

> 🚀 **[Повторить с AI Studio →](https://aistudio.yandex.ru/platform?utm_source=github&utm_medium=owned&utm_campaign=t:info;gl:lgen&utm_content=cookbook_cb_omniagent)**

# Архитектура решения

[Схема взаимодействия агента](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=omniagent.drawio&dark=auto#R%3Cmxfile%3E%3Cdiagram%20name%3D%22%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0%201%22%20id%3D%22u4aH2y1j8b5d2v2d1W9M%22%3E5Vhbb%2BI4FP41kToPs8qFhPBIgHarmZFQg9Tdp8okTuKpiSPHKbC%2Ffk8ch1w7gk6pKg1IwTk%2Bx5fv%2B2wfo1mL3eGOoyz5wUJMNVMPD5q11EzT0KcW%2FJSWY2Vxpm5liDkJlVNj8Ml%2FuI5U1oKEOO84CsaoIFnXGLA0xYHo2BDnbN91ixjt9pqhGA8MfoDo0PpIQpFUVtecNva%2FMYmTumfDmVU1O1Q7q5nkCQrZvmWyVpq14IyJqrQ7LDAtwatxqeJuX6k9DYzjVJwTsMfbJ5IKzCMU4GGwai8Xx3rqnBVpiMtoQ7O8fUIE9rMy1lrugWywJWJHVXVEKF0wyriMtaIoMoMA7Lng7Bm3akJn69gO1FT9vSBaqP60pa7N5NOz5dP4Kn9c%2BVxq0I97qoayLp%2BTVsBMWmAmDnQECrK8m1vOYM5p%2BEV1h7nAh9aMFVZ3mO2w4EdwSVp0Ooq7fUO9UfOpWplY6l0J3HDVO1LKi09NN%2BRAQfEzztUWBc8w6Kuz5AZ4nKWta09s%2FVWWDAn0UoI%2BbxFQWSZAAIUBe1sOpbgs3ayPImEpNOVVU%2FswPiz9HfjIOHuBfYjn5zACobA74YvZwEZo4%2BkYGzNnaqHxNaOQDslLDfW%2FCPRwALcFZUVYO8AMWz7ze6j3RRES9iYeTqBfQESpp98m4ign9xRn4uprwy6%2FY2w48jPGxgn6u%2FXmTbhaQ1jdLqrWrIeq8w6ocozgRN3hJ5SRz4jrA4xvA%2BMD63x9fyVkbeMKyJZpicIPh4NM45e7CLj76pVx2DxjliK6aqxew0K5UTc%2B3xnLFPY%2FsRBHlVShQrAuM7ANz8sUCV63lAXPlemW0NqhGpRAPMbi1SSisxuN0cAxRYK8dCc%2FBqoKXTPooaV4u8uL2d%2FQc1bwAKuoHjWnYZzNlnkBW7LjV4H5ZGQO1lsU6fAZpbmTf%2Fz6uHlY%2BZt6XY4dNY9468NwsLhAHIp5%2FS9jYs7O1kvtwqIoxx0pDDQ1mfQ0Ne1pqgLjvTRl%2FTGaKhUVRRdq6nJd6PrM%2FghdnE7b6%2Bhi8jZddJD8ZIoY8t7LnVvMyz1Dl1cGU14oPFmeyueqY2%2Fd6Ab%2BRu0v74SqwUWrkfYVsQpxv%2FzmUXXu%2Bf%2B48f6ZicR%2FsDdP%2FvP996j49vDVPOf8zxOUlcViR%2BeBKNeXV6Y8JAC20BbTNcuJIHClAiaYEGzXcphTEpcVgvVyMVYISlJYsPWfJaNXvKq%2Fd7qfWb38tZdlGf2d9wyU4bX526Raes2fT9bqfw%3D%3D%3C%2Fdiagram%3E%3C%2Fmxfile%3E)

#### Описание взаимодействия компонентов

Бэкенд взаимодействует с моделями Yandex AI Studio в текстовом и голосовом режиме. Веб-интерфейс общается с бэкенд-приложением (прокси-агентом) по протоколам HTTP и WebSocket.

#### Список используемых сервисов

* **Yandex AI Studio** — API для работы с моделями.
* **Compute Cloud**, **Serverless Containers** — развертывание приложения.

#### Роли для используемых сервисов

| Сервис           | Назначение                                 | Роли для сервисного аккаунта       |
|------------------|--------------------------------------------|------------------------------------|
| Yandex AI Studio | Для работы с Realtime API                  | `ai.models.editor`                 |
| Yandex AI Studio | Для работы с текстовыми моделями           | `ai.assistants.editor`             |

# Подготовка окружения и развёртывание инфраструктуры

### Подготовка сервисного аккаунта AI Studio

1. Создайте сервисный аккаунт с правами `ai.models.editor` и `ai.assistants.editor` по [инструкции](https://yandex.cloud/ru/docs/iam/operations/sa/create).
2. Создайте ключ и сохраните значение **Secret key**.

### Подготовка окружения

1. Создайте виртуальную машину согласно [документации](https://yandex.cloud/ru/docs/compute/quickstart/quick-create-linux). В примере будет использоваться Ubuntu 24.04 LTS.

2. Подключитесь к ВМ (виртуальной машине) и установите ПО:

   ```
   ssh {адрес или имя созданной ВМ}
   sudo apt install python3-venv  python3-pip unzip
   ```

### Установка агента

- В консоли ВМ склонируйте проект.

```
git clone https://github.com/yandex-ai-studio/ai-academy-cb-omniagent.git
```

- Перейдите в папку **omniagent**:

  `cd ai-academy-cb-omniagent`

- Создайте виртуальное окружение Python (опционально) и активируйте его, установите зависимости.

```
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
```

- Добавьте ключи и проект в качестве переменных окружения на ВМ.

  ```
  export API_KEY=AQVN3dygsh8GnfRJxxFxxnANAxxMifm_xxxxxx
  export PROJECT=b1gsl7pdl5v5xxxxxxxx
  
  ```
- Запустите приложение:

```
python3 index.py
```

Должен появиться вывод в консоль:
"Starting Chat Support Bot Server"
"Server URL: http://0.0.0.0:8000"

- Для проверки развертывания откройте в браузере адрес ВМ: `http://{адрес-ВМ}`.

- Браузер требует защищённое соединение по TLS/HTTPS для использования API микрофона. Для тестирования можно использовать незащищенное соединение с локальным хостом (127.0.0.1:8000) — пробросьте порт через SSH-туннель:

```
ssh -L 8000:127.0.0.1:8000 {адрес вм}
```

## Логика приложения / сценарий использования

#### Взаимодействие в текстовом режиме

Для взаимодействия в текстовом режиме откройте [эту страницу](http://localhost:8000/static/).

#### Взаимодействие в голосовом режиме

Для взаимодействия в голосовом режиме откройте [эту страницу](http://localhost:8000/static/), переключитесь в режим голоса в интерфейсе и нажмите на кнопку записи речи.

## Результаты и выводы

Текстовый режим работает так же, как текстовый агент Yandex AI Studio: дает доступ к выбору инструментов и языковых моделей из Model Gallery.

Голосовой режим работает на отдельной быстрой модели для распознавания речи. Чтобы снизить задержку в общении, у нее уменьшено контекстное окно.

### Очистка ресурсов

Удалите сервисный аккаунт и ВМ.

### Полезные ссылки

Ссылки на официальную документацию Yandex Cloud:

- [Создание виртуальной машины](https://yandex.cloud/ru/docs/compute/quickstart/quick-create-linux)
- [Создание сервисного аккаунта](https://yandex.cloud/ru/docs/iam/operations/sa/create)
- [Создание поискового индекса по файлам](https://aistudio.yandex.ru/docs/ru/ai-studio/operations/agents/vectorstore-create-ui.html)
