#!./ENV/bin/python3

# Websockets server

import asyncio
import json
import logging
import websockets

from settings import *

logging.basicConfig()

# key:      websocket
# value:    user_uuid пользователя, который подключился к websocket,
#           или None id, если в браузере, подключившемся к websocket,
#           не был выполнен login
#
WEBSOCKETS = {}

# key:      user_uuid
# value:    set of websockets, к которым подключились браузеры,
#           в которых пользователь user_uuid выполнил login
#
USERS = {}

async def register(websocket):
    WEBSOCKETS[websocket] = None
    message = json.dumps({
        'event': 'connect',
        'n_sessions': len(WEBSOCKETS),
        'n_users': len(USERS),
    })
    await asyncio.wait([ws.send(message) for ws in WEBSOCKETS.keys()])

async def unregister(websocket):
    user_uuid = WEBSOCKETS.get(websocket)
    if user_uuid:
        websockets = USERS.get(user_uuid)
        if websockets:
            try:
                websockets.remove(websocket)
                if not websockets:
                    del USERS[user_uuid]
            except KeyError:
                pass
    try:
        del WEBSOCKETS[websocket]
    except KeyError:
        pass
    if WEBSOCKETS:
        message = json.dumps({
            'event': 'disconnect',
            'n_sessions': len(WEBSOCKETS),
            'n_users': len(USERS),
            'logged_out_user_uuid': user_uuid,
        })
        await asyncio.wait([ws.send(message) for ws in WEBSOCKETS.keys()])

async def handler(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except ValueError:
                data = {}

            if data.get('action') == "login":
                user_uuid = data.get('user_uuid')
                if user_uuid:
                    send_message = False
                    if user_uuid not in USERS:
                        USERS[user_uuid] = set()
                        send_message = True
                    USERS[user_uuid].add(websocket)
                    WEBSOCKETS[websocket] = user_uuid
                    if send_message and USERS:
                        message = json.dumps({
                            'event': 'login',
                            'n_sessions': len(WEBSOCKETS),
                            'n_users': len(USERS),
                            'user_uuid': user_uuid,
                        })
                        await asyncio.wait([ws.send(message) for ws in WEBSOCKETS.keys()])

            elif data.get('action') == "addoperation":
                user_id_from = data.get('user_id_from')
                user_id_to =   data.get('user_id_to')
                operation_type_id = data.get('operation_type_id')
                if user_id_from and user_id_to and operation_type_id:
                    user_to_websockets = USERS.get(user_id_to)
                    if user_to_websockets:
                        data['event'] = data['action']
                        del data['action']
                        del data['user_id_to']
                        data.update({
                            'n_sessions': len(WEBSOCKETS),
                            'n_users': len(USERS),
                        })
                        message = json.dumps(data)
                        await asyncio.wait([ws.send(message) for ws in user_to_websockets])
            else:
                logging.error("unsupported action: {}", data)
    finally:
        await unregister(websocket)

start_server = websockets.serve(handler, host='127.0.0.1', port=SERVER_PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
