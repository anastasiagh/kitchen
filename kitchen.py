import requests
from flask import Flask, request
import queue
import time
from itertools import count
from operator import itemgetter
import threading
import logging
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

TIME_UNIT = 1

orders_list = []
cooks_list = [{
    "id": 1,
    "rank": 3,
    "proficiency": 4,
    "name": "Guy Fieri",
    "catch-phrase": "Cooking is like snow skiing: If you don’t fall at least 10 times, then you’re not skiing hard enough"
}, {
    "id": 2,
    "rank": 3,
    "proficiency": 3,
    "name": "Gordon Ramsay",
    "catch-phrase": "Cooking is about passion, so it may look slightly temperamental in a way that it’s too assertive to the naked eye"
}, {
    "id": 3,
    "rank": 2,
    "proficiency": 3,
    "name": "Bobby Flay",
    "catch-phrase": "Grilling takes the formality out of entertaining. Everyone wants to get involved"
},  {
    "id": 4,
    "rank": 1,
    "proficiency": 2,
    "name": "Rachael Ray",
    "catch-phrase": "Yum-O!"
}]

menu = [{
    "id": 1,
    "name": "pizza",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 2,
    "name": "salad",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": None
}, {
    "id": 4,
    "name": "Scallop Sashimi with Meyer Lemon Confit",
    "preparation-time": 32,
    "complexity": 3,
    "cooking-apparatus": None
}, {
    "id": 5,
    "name": "Island Duck with Mulberry Mustard",
    "preparation-time": 35,
    "complexity": 3,
    "cooking-apparatus": "oven"
}, {
    "id": 6,
    "name": "Waffles",
    "preparation-time": 10,
    "complexity": 1,
    "cooking-apparatus": "stove"
}, {
    "id": 7,
    "name": "Aubergine",
    "preparation-time": 20,
    "complexity": 2,
    "cooking-apparatus": None
}, {
    "id": 8,
    "name": "Lasagna",
    "preparation-time": 30,
    "complexity": 2,
    "cooking-apparatus": "oven"
}, {
    "id": 9,
    "name": "Burger",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": "oven"
}, {
    "id": 10,
    "name": "Gyros",
    "preparation-time": 15,
    "complexity": 1,
    "cooking-apparatus": None
}]

app = Flask(__name__)

@app.route('/order', methods=['POST'])
def order():
    response = request.get_json()
    logging.info(f'New order received from dinnig hall server: order id {response["order_id"]} items : {response["items"]} priority : {response["priority"]}' )
    # print(response)
    split_response(response)
    return {'isSuccess': True}


def split_response(received_order):
    kitchen_order = {
        'order_id': received_order['order_id'],
        'table_id': received_order['table_id'],
        'waiter_id': received_order['waiter_id'],
        'items': received_order['items'],
        'priority': received_order['priority'],
        'max_wait': received_order['max_wait'],
        'received_time': time.time(),
        'cooking_details': queue.Queue(),
        'prepared_items': 0,
        'time_start': received_order['time_start'],
    }
    orders_list.append(kitchen_order)
    for index in received_order['items']:
        food_item = next((food for i, food in enumerate(menu) if food['id'] == index), None)
        if food_item is not None:
            foods_queue.put_nowait((received_order['priority'], next(counter),{
                'food_id': food_item['id'],
                'order_id': received_order['order_id'],
                'priority': int(received_order['priority'])
            }))


def cooking_process(cook, stoves_queue, ovens_queue, food_items):
    print(cook)
    while True:
        try:
            item = food_items.get_nowait()
            food_item = item[2]
            curr_counter = item[1]
            # print(food_item)
            # print(curr_counter)
            # print(curr_counter)
            food_details = next((food for food in menu if food['id'] == food_item['food_id']), None)
            (index, order_details) = next(((index, order) for index, order in enumerate(orders_list) if order['order_id'] == food_item['order_id']), (None, None))
            len_order_items = len(orders_list[index]['items'])
            if food_details['complexity'] == cook['rank'] or food_details['complexity'] == cook['rank'] - 1:
                cooking_aparatus = food_details['cooking-apparatus']
                if cooking_aparatus is None:
                    logging.info(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} manually')
                    time.sleep(food_details['preparation-time'] * TIME_UNIT)
                    logging.info(f'{threading.current_thread().name}  finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} manually')
                elif cooking_aparatus == 'oven':
                    oven = ovens_queue.get_nowait()
                    logging.info(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on oven {oven} ')
                    time.sleep(food_details['preparation-time'] * TIME_UNIT)
                    size = ovens_queue.qsize()
                    ovens_queue.put_nowait(size)
                    logging.info(f'{threading.current_thread().name} finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on oven {oven} ')
                elif cooking_aparatus == 'stove':
                    stove = stoves_queue.get_nowait()
                    logging.info(f'{threading.current_thread().name} cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on stove {stove} ')
                    time.sleep(food_details['preparation-time'] * TIME_UNIT)
                    size = stoves_queue.qsize()
                    stoves_queue.put_nowait(size)
                    logging.info(f'{threading.current_thread().name}  finished cooking food {food_details["name"]}: with Id {food_details["id"]} for order {order_details["order_id"]} on stove {stove} ')


                orders_list[index]['prepared_items'] += 1
                if orders_list[index]['prepared_items'] == len_order_items:
                    logging.info(f'{threading.current_thread().name} cook has finished the order {order_details["order_id"]}')
                    orders_list[index]['cooking_details'].put({'food_id': food_details['id'], 'cook_id': cook['id']})
                    finish_preparation_time = int(time.time())
                    logging.info(f'Calculating')
                    payload = {
                        **orders_list[index],
                        'cooking_time': finish_preparation_time - int(orders_list[index]['received_time']),
                        'cooking_details': list(orders_list[index]['cooking_details'].queue)
                    }
                    requests.post('http://localhost:3000/distribution', json=payload, timeout=0.0000000001)
                    # print(payload)


            else:
                food_items.put_nowait((food_item['priority'], curr_counter, food_item))

        except Exception as e:
            pass


def cooks_cooking_process(cook, ovens, stoves, food_items):
    for index in range(cook['proficiency']):
        task_thread = threading.Thread(target=cooking_process, args=(cook, ovens, stoves, food_items), daemon=True, name=f'{cook["name"]}-Task {index}')
        task_thread.start()

if __name__ == '__main__':
    foods_queue = queue.PriorityQueue()
    stoves_queue = queue.Queue()
    ovens_queue = queue.Queue()
    stoves_queue.put_nowait(0)
    stoves_queue.put_nowait(1)
    stoves_queue.put_nowait(2)
    stoves_queue.put_nowait(3)
    ovens_queue.put_nowait(0)
    ovens_queue.put_nowait(1)
    ovens_queue.put_nowait(2)
    ovens_queue.put_nowait(3)
    counter = count(start=1, step=1)
    main_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=3030, debug=False, use_reloader=False), daemon=True)
    main_thread.start()

    for _, cook in enumerate(cooks_list):
        cook_thread = threading.Thread(target=cooks_cooking_process, args=(cook,ovens_queue,stoves_queue, foods_queue), daemon=True)
        cook_thread.start()

    while True:
        pass
