#импорт модулей
import asyncio
import logging
import json
import random
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Union, Any, Dict, Sequence, Literal
from typing import List
from faststream import FastStream
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

# Конструктор RabbitBroker
broker = RabbitBroker("amqps://user:password@host:1111/vhost")

#Определение обменников
exch_1 = RabbitExchange("InputsFanoutExchange", type=ExchangeType.FANOUT)
exch_2 = RabbitExchange("AppsTopicExchange", type=ExchangeType.TOPIC, bind_to=exch_1, routing_key="app.#")
exch_3 = RabbitExchange("QuestionsHeadersExchange", type=ExchangeType.HEADERS,bind_arguments={"subject": "question", "theme": "delivery", "x-match": "all"})

#Определение очередей
queue_1 = RabbitQueue("InputsQueue")
queue_2 = RabbitQueue("CorpAppsQueue", routing_key="app.company.*")
queue_3 = RabbitQueue("IndAppsQueue", routing_key="app")
queue_4 = RabbitQueue("DeliveryQueue", bind_arguments={"subject": "question", "theme": "delivery", "x-match": "all"})
queue_5 = RabbitQueue("PaymentQueue", bind_arguments={"subject": "question", "theme": "payment", "x-match": "all"})
queue_6 = RabbitQueue("OtherQuestionsQueue", bind_arguments={"subject": "question", "theme": "vip", "x-match": "all"})

# Инициализация FastStream приложения
app = FastStream(broker)

# Определение классов
# Базовый класс для запросов
@dataclass
class RequestData:
    moment: datetime
    name: str
    subject: str
    content: str

# Класс для корпоративных запросов
@dataclass
class CorporateRequest(RequestData):
    inn: str

# Класс для частных запросов
@dataclass
class PrivateRequest(RequestData):
    phone_number: str
    age: int

# Класс для заявок с темой "question"
@dataclass
class QuestionRequest(RequestData):
    priority: int

# Варианты ключей маршрутизации
corp = random.choice([1, 0])

if corp == 1:
    name = 'company.name'
    routing_keys = [f'app.company.{name}', 'question']
else:
    routing_keys = ['app', 'question']

# Случайный выбор одного из ключей маршрутизации
subject = random.choice(routing_keys)

# Варианты заголовков маршрутизации
questions = ['payment', 'delivery', 'discount', 'vip', 'staff']
theme = random.choice(questions)

# Варианты схем публикуемых сообщений
RequestSchema = Union[CorporateRequest, PrivateRequest, QuestionRequest]

# Публикация сообщений в exch_1
@broker.publisher(exchange=exch_1, routing_key=subject, headers={'subject': subject, 'theme':theme})
async def publish_request(request: RequestSchema):
    logging.info(f"Публикация запроса: {asdict(request)}")
    return request

# Подписка на очередь queue_1
@broker.subscriber(queue=queue_1, exchange=exch_1)
async def handle_inputs_queue(request: RequestSchema):
    logging.info(f"Получен запрос из InputsQueue: {asdict(request)}")

# Подписка на очереди, связанные с exch_2
@broker.subscriber(queue=queue_2, exchange=exch_2)
async def handle_corp_apps_queue(request: CorporateRequest):
    logging.info(f"Получен корпоративный запрос из CorpAppsQueue: {asdict(request)}")

@broker.subscriber(queue=queue_3, exchange=exch_2)
async def handle_ind_apps_queue(request: PrivateRequest):
    logging.info(f"Получен частный запрос из IndAppsQueue: {asdict(request)}")

# Подписка на очереди, связанные с exch_3
@broker.subscriber(queue=queue_4, exchange=exch_3, consume_args={"subject": "question", "theme": "delivery", "x-match": "all"})
async def handle_delivery_queue(request: QuestionRequest):
    logging.info(f"Получен запрос по доставке из DeliveryQueue: {asdict(request)}")

@broker.subscriber(queue=queue_5, exchange=exch_3, consume_args={"subject": "question", "theme": "payment", "x-match": "all"})
async def handle_payment_queue(request: QuestionRequest):
    logging.info(f"Получен платежный запрос из PaymentQueue: {asdict(request)}")

@broker.subscriber(queue=queue_6, exchange=exch_3, consume_args={"subject": "question", "theme": {theme}, "x-match": "all"})
async def handle_other_questions_queue(request: QuestionRequest):
    logging.info(f"Получен VIP запрос из OtherQuestionsQueue: {asdict(request)}")