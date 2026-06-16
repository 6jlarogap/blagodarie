# handler_offer.py
#
# Команды и сообщения для offer: наши опросы/предложения

import re
from uuid import uuid4

from aiogram import Router, F, types, html
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ContentType, \
                          InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.enums.message_entity_type import MessageEntityType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.state import StatesGroup, State

from handler_bot import is_it_command

import logging
import settings 

from common import Misc, KeyboardType, TgGroup, TgGroupMember, Rcache, TgDesc
import me
dp, bot, bot_data = me.dp, me.bot, me.bot_data

router = Router()

class FSMofferPlace(StatesGroup):
    # После создания оффера спросить о месте
    ask = State()

class FSMofferPutDesc(StatesGroup):
    # изменить описание существующего оффера
    ask = State()

class FSMofferChoiceDonate(StatesGroup):
    # отправить донат по поводу выбора из офера
    ask = State()

class FSMsendMessageToOffer(StatesGroup):
    ask = State()

class FSMOfferPutPlace(StatesGroup):
    # изменить место существующего оффера
    ask = State()

class Offer(object):

    PROMPT_OFFER_GEO = 'Укажите координаты опроса вида: хх.ххх,уу.ууу - их удобно скопировать из карт яндекса или гугла'

    @classmethod
    async def get_offer(cls, **kwargs):
        """
        Получить минимум сведений об офере

        Возможные параметры (**kwargs):
            Обязательно:
                offer_id
                    или
                offer_uuid
            Возможно:
            user_ids_only = 'on'
        """
        logging.debug('get_offer_data, params: %s' % kwargs)
        status, response = await Misc.api_request(
            path='/api/offer',
            method='get',
            params=kwargs,
        )
        logging.debug('get_offer_data, status: %s' % status)
        logging.debug('get_offer_data, response: %s' % response)
        return status, response


    @classmethod
    async def cmd_offer(cls, message: Message, state: FSMContext):
        """
        Создание опроса- предложения из сообщения- команды

        offer:          опрос c выбором лишь одного ответа
        offer_multi:    опрос с возможным выбором нескольких ответов
        """
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender == 200:
            answers = []
            err_mes = ''
            for i, l in enumerate(message.text.split('\n')):
                line = l.strip()
                if not line:
                    continue
                if i == 0:
                    m = re.search(r'^\/(offer|offer_multi)\s+(.*)$', line, flags=re.I)
                    if not m or not m.group(2):
                        err_mes = 'Не указан вопрос опроса'
                        break
                    question = m.group(2)
                    is_multi = m.group(1).lower() == 'offer_multi'
                else:
                    for a in answers:
                        if line == a:
                            err_mes = 'Обнаружен повтор ответа'
                            break
                    if err_mes:
                        break
                    answers.append(line)
            if not err_mes:
                if not answers:
                    err_mes = 'Не указаны ответы'
                elif len(answers) > settings.OFFER_MAX_NUM_ANSWERS:
                    err_mes = 'Превышен максимум числа ответов (до %s)' % settings.OFFER_MAX_NUM_ANSWERS
            if err_mes:
                help_mes = (
                    '%(err_mes)s\n\n'
                    'Поручить боту создать опрос-предложение:\n'
                    '\n'
                    '/offer Вопрос\n'
                    '<i>или</i>\n'
                    '/offer_multi Вопрос\n'
                    'Ответ 1\n'
                    'Ответ 2\n'
                    ' и т.д. не больше %(offer_max_num_answers)s ответов\n'
                    '\n'
                    '/offer: опрос c выбором лишь одного ответа\n'
                    '/offer_multi: опрос с возможным выбором нескольких ответов\n'
                    '\n'
                    'Используйте \\n для перевода строки в Вопросе\n'
                )
                await message.reply(help_mes % dict(
                    err_mes=err_mes,
                    offer_max_num_answers=settings.OFFER_MAX_NUM_ANSWERS
                ))
                return

            await state.update_data(
                create_offer_dict=dict(
                    user_uuid=response_sender['uuid'],
                    question=question.replace('\\n', '\n'),
                    answers=answers,
                    is_multi=is_multi,
            ))
            inline_btn_pass = InlineKeyboardButton(
                text='Пропустить',
                callback_data=Misc.CALLBACK_DATA_KEY_TEMPLATE % dict(
                    keyboard_type=KeyboardType.OFFER_GEO_PASS,
                    sep=KeyboardType.SEP,
            ))
            await state.set_state(FSMofferPlace.ask)
            await message.reply(
                cls.PROMPT_OFFER_GEO,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[inline_btn_pass, Misc.inline_button_cancel()]]
            ))

    @classmethod
    async def put_offer_properties(cls, **kwargs):
        """
        Изменить свойства офера
        """
        status, response = None, None
        logging.debug('put offfer_data...')
        payload = dict(tg_token=settings.TOKEN,)
        payload.update(**kwargs)
        logging.debug('put offer_data, payload: %s' % Misc.secret(payload))
        status, response = await Misc.api_request(
            path='/api/offer',
            method='put',
            json=payload,
        )
        logging.debug('put offer_data, status: %s' % status)
        logging.debug('put offer_data, response: %s' % response)
        return status, response


    @classmethod
    async def create_offer(cls, data, response_sender, message):
        create_offer_dict = data['create_offer_dict']
        create_offer_dict.update(tg_token=settings.TOKEN)
        logging.debug('create offer in api, payload: %s' % Misc.secret(create_offer_dict))
        status, response = await Misc.api_request(
            path='/api/offer',
            method='post',
            json=create_offer_dict,
        )
        logging.debug('create offer in api, status: %s' % status)
        logging.debug('create offer in api, response: %s' % response)
        err_mes = ''
        if status == 400 and response.get('message'):
            err_mes = response['message']
        elif status != 200:
            err_mes = 'Ошибка сохранения опроса-предложения'
        if err_mes:
            await message.reply(err_mes)
            return
        await message.reply('Создан опрос:')
        await cls.show_offer(
            response_sender, response, message,
            username_href=response_sender['username'],
            profile_ref=response_sender,
        )


    @classmethod
    async def offer_forwarded_in_group_or_channel(cls, message, state):
        result = False
        if message.forward_origin:
            offer_uuid, username_href = cls.get_data_from_offer_message(message)
            if offer_uuid:
                status_offer, response_offer = await cls.post_offer_answer(offer_uuid, None, [-1])
                if status_offer == 200:
                    await cls.show_offer(
                        user_from=None,
                        offer=response_offer['offer'],
                        message=message,
                        username_href=username_href
                    )
                    result = True
                    try:
                        await message.delete()
                    except TelegramBadRequest:
                        pass
        return result


    @classmethod
    def get_data_from_offer_message(cls, message):
        if message.content_type == ContentType.TEXT:
            username_href = None
            num_links = 0
            for entity in message.entities:
                m = None
                if entity.type == MessageEntityType.TEXT_LINK:
                    m = re.search((
                            r'(?:start\=offer\-|offer_uuid\=|offer_id\=)'
                            r'([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})'
                            r'(?:-userId-([a-z0-9]{10})){0,1}'
                        ),
                        entity.url,
                        flags=re.I
                    )
                if m:
                    num_links += 1
                    offer_uuid = m.group(1)
                    if m2 := m.group(2):
                        username_href = m2
                if num_links >= 2:
                    return offer_uuid, username_href
        return None, None


    @classmethod
    async def show_offer(
        cls,
        user_from, offer, message,
        username_href=None,
        profile_ref=None
    ):
        """
        Показать опрос-предложение

        Текст получаем из text_offer(), формируем сообщение с этим текстом и с кнопками:
        Ответ 1
        Ответ 2
        ...
        Ответ N
        Отмена
        Обновить
        Кнопки будут иметь свой keyboard_type, uuid опроса, а также номер ответа:
            - для ответов 1 ... N номер будет: 1 ... N
            - для Отмена: 0
            - для Обновить: -1

        Структура offer на входе имееет вид:
        {
            'uuid': '6caf0f7f-d9f4-4c4f-a04b-4a9169f7461c',
            'owner': {'first_name': 'Евгений Супрун', 'uuid': '8f686101-c5a2-46d0-a5ee-c74386ffffff', 'user_id': 326},
            'question': 'How are you',
            'timestamp': 1683197002,
            'closed_timestamp': None,
            'is_multi': True,
            'answers': [
                {
                    'number': 0,        // ответ с фиктивным номером 0: тот кто видел опрос, возможно голосовал
                    'answer': '',       // и отменил голос
                    'users': [
                        { 'user_id': 326, 'uuid': '8f686101-c5a2-46d0-a5ee-c74386ffffff', 'first_name': 'X Y'}
                    ]
                },
                { 'number': 1, 'answer': 'Excellent', 'users': [] },
                { 'number': 2, 'answer': 'Good', 'users': [] },
                { 'number': 3, 'answer': 'Bad', 'users': []  }
            ],
            'user_answered': {'326': {'answers': [0]}} // создатель опроса его видел
        }
        username_href:  имя userId= в ссылке на опрос
        profile_ref:    имя его в кнопках опроса

        """
        try:
            await bot.send_message(
                message.chat.id,
                text=cls.text_offer(
                    user_from, offer, message,
                    username_href, profile_ref,
                ),
                reply_markup=cls.markup_offer(
                    user_from, offer, message,
                    username_href, profile_ref,
            ))
        except (TelegramBadRequest, TelegramForbiddenError,):
            await message.reply('Опрос-предложение предъявить не удалось')


    @classmethod
    def get_deeplink(cls, offer_uuid, username_href=None):
        href = f't.me/{bot_data.username}?start=offer-{offer_uuid}'
        if username_href:
            href += f'-userId-{username_href}'
        return href


    @classmethod
    def text_offer(
            cls,
            user_from, offer, message,
            username_href=None, profile_ref=None
        ):
        """
        Текст опроса-предложения

        На примере опроса 'Как дела?' с ответами Отлично (3 голоса), Хорошо (2), Плохо (0)

        Как дела?

        Голоса на <датавремя>
        Отлично - 3
        Хорошо - 2
        Плохо - 0

        Схема <d3.doverabot.ru/?offer_uuid=offerUUID>
        Карта map.doverabot.ru/?offer_id=offerUUID
        Ссылка на опрос <t.me/bot_username?start=offer-offerUUID>

        Это всё сообщение - под ним - 5 кнопок:
        Отлично
        Хорошо
        Плохо
        Отмена
        Обновить результаты
        """
        result = (
            '%(question)s\n'
            '%(multi_text)s%(closed_text)s'
            '\n'
            '<i>Голоса</i> на %(datetime_string)s\n'
        ) % dict(
            question=offer['question'],
            datetime_string=Misc.datetime_string(offer['timestamp'], with_timezone=True),
            multi_text='(возможны несколько ответов)\n' if offer['is_multi'] else '',
            closed_text='(опрос остановлен)\n' if offer['closed_timestamp'] else '',
        )
        for answer in offer['answers']:
            if answer['number'] > 0:
                result += '<i>%s</i> - %s\n' % (html.quote(answer['answer']), len(answer['users']),)
        result += '\n'

        username_href = username_href or (user_from and user_from['username']) or None
        result += Misc.get_html_a(
            href=Offer.get_deeplink(offer["uuid"], username_href),
            text='Ссылка на предложение'
        ) + '\n'

        result += Misc.get_html_a(
            href='%s/?offer_uuid=%s' % (settings.GRAPH_HOST, offer['uuid']),
            text='Схема'
        ) + '\n'
        result += Misc.get_html_a(
            href='%s/?offer_id=%s' % (settings.MAP_HOST, offer['uuid']),
            text='Карта'
        ) + '\n'

        if profile_ref:
            result += Misc.get_html_a(
                href=Misc.get_deeplink(profile_ref, https=True),
                text='Реферер: ' + profile_ref['first_name']
            ) + '\n'

        result += Misc.get_html_a(
            href=Misc.get_deeplink(offer['owner'], https=True),
            text='Автор: ' + offer['owner']['first_name']
        ) + '\n'

        return result


    @classmethod
    def markup_offer(
            cls,
            user_from, offer, message,
            username_href=None, profile_ref=None
        ):
        buttons = []
        message_chat_type = message.chat.type if message else ChatType.PRIVATE
        callback_data_template = '%(keyboard_type)s%(sep)s%(uuid)s%(sep)s%(number)s%(sep)s'
        if profile_ref:
            callback_data_template += '%(username_ref)s%(sep)s'
        callback_data_dict = dict(
            keyboard_type=KeyboardType.OFFER_ANSWER,
            uuid=offer['uuid'],
            sep=KeyboardType.SEP,
            username_ref=profile_ref['username'] if profile_ref else ''
        )
        if not offer['closed_timestamp']:
            have_i_voted = False
            for answer in offer['answers']:
                if answer['number'] > 0:
                    callback_data_dict.update(number=answer['number'])
                    answer_text = answer['answer']
                    if user_from and user_from['user_id'] in answer['users']:
                        have_i_voted = True
                        if message_chat_type == ChatType.PRIVATE:
                            answer_text = '(*) ' + answer_text
                    inline_btn_answer = InlineKeyboardButton(
                        text=answer_text,
                        callback_data=callback_data_template % callback_data_dict
                    )
                    buttons.append([inline_btn_answer])

            if have_i_voted or message_chat_type != ChatType.PRIVATE:
                callback_data_dict.update(number=0)
                inline_btn_answer = InlineKeyboardButton(
                    text='Отозвать мой выбор',
                    callback_data=callback_data_template % callback_data_dict
                )
                buttons.append([inline_btn_answer])

        callback_data_dict.update(number=-1)
        inline_btn_answer = InlineKeyboardButton(
            text='Обновить результаты',
            callback_data=callback_data_template % callback_data_dict
        )
        buttons.append([inline_btn_answer])

        if message_chat_type == ChatType.PRIVATE and user_from['uuid'] == offer['owner']['uuid']:
            callback_data_dict.update(number=-2)
            inline_btn_answer = InlineKeyboardButton(
                text='Сообщение участникам',
                callback_data=callback_data_template % callback_data_dict
            )
            buttons.append([inline_btn_answer])

            if offer['closed_timestamp']:
                callback_data_dict.update(number=-4)
                inline_btn_answer = InlineKeyboardButton(
                    text='Возбновить опрос',
                    callback_data=callback_data_template % callback_data_dict
                )
            else:
                callback_data_dict.update(number=-3)
                inline_btn_answer = InlineKeyboardButton(
                    text='Остановить опрос',
                    callback_data=callback_data_template % callback_data_dict
                )
            buttons.append([inline_btn_answer])

            callback_data_dict.update(number=-5)
            inline_btn_answer = InlineKeyboardButton(
                text='Задать координаты',
                callback_data=callback_data_template % callback_data_dict
            )
            buttons.append([inline_btn_answer])

        if message_chat_type == ChatType.PRIVATE and \
           (user_from['uuid'] == offer['owner']['uuid'] or offer['desc']):
            callback_data_dict.update(number=-6)
            inline_btn_answer = InlineKeyboardButton(
                text='Описание',
                callback_data=callback_data_template % callback_data_dict
            )
            buttons.append([inline_btn_answer])
        return InlineKeyboardMarkup(inline_keyboard=buttons)


    @classmethod
    async def post_offer_answer(cls, offer_uuid, user_from, answers, **kwargs):
        payload = dict(
            tg_token=settings.TOKEN,
            offer_uuid=offer_uuid,
            answers=answers,
            user_uuid=user_from and user_from['uuid'] or None,
        )
        payload.update(kwargs)
        logging.debug('post_offer, payload: %s' % Misc.secret(payload))
        status, response = await Misc.api_request(
            path='/api/offer/answer',
            method='post',
            json=payload,
        )
        logging.debug('post_offer_answer, status: %s' % status)
        logging.debug('get_offer_answer, response: %s' % response)
        return status, response


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMofferPlace.ask))
async def process_offer_location(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + \
            Offer.PROMPT_OFFER_GEO,
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or not data.get('create_offer_dict') or \
        profile_from['uuid'] != data['create_offer_dict']['user_uuid']:
        await state.clear()
        return
    latitude, longitude = Misc.check_location_str(message.text)
    if latitude is None or longitude is None:
        error_message = Misc.MSG_ERR_GEO + '\n\n' + Offer.PROMPT_OFFER_GEO
        inline_btn_pass = InlineKeyboardButton(
            text='Пропустить',
            callback_data=Misc.CALLBACK_DATA_KEY_TEMPLATE % dict(
                keyboard_type=KeyboardType.OFFER_GEO_PASS,
                sep=KeyboardType.SEP,
        ))
        await message.reply(
            error_message,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[inline_btn_pass, Misc.inline_button_cancel()]]
        ))
        return
    data['create_offer_dict']['latitude'], data['create_offer_dict']['longitude'] = latitude, longitude
    await state.clear()
    await Offer.create_offer(data, profile_from, message)


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.OFFER_GEO_PASS,
        KeyboardType.SEP,
        )), StateFilter(FSMofferPlace.ask))
async def cbq_offer_geo_pass(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    await state.clear()
    if status_from == 200 and data.get('create_offer_dict') and \
       profile_from['uuid'] == data['create_offer_dict']['user_uuid']:
        await Offer.create_offer(data, profile_from, callback.message)
    await callback.answer()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.OFFER_ANSWER,
        KeyboardType.SEP,
        )), StateFilter(None))
        # uuid опроса           # 1
        # KeyboardType.SEP,
        # номер ответа          # 2
        #   >= 1:   подать голос
        #      0:   отозвать голос
        #     -1:   обновить результаты
        #     -2:   сообщение, пока доступно только владельцу опроса
        #     -3:   остановить опрос
        #     -4:   возобновить опрос
        #     -5:   задать координаты
        #     -6:   ввести/оказать описание
        # KeyboardType.SEP,
        # профиль реферера (кому донатить)
        #
async def cbq_offer_answer(callback: CallbackQuery, state: FSMContext):
    tg_user_sender = callback.from_user
    code = callback.data.split(KeyboardType.SEP)
    try:
        offer_uuid = code[1]
        number = int(code[2])
    except (IndexError, ValueError,):
        return
    try:
        username_ref = code[3]
    except (IndexError, ValueError,):
        username_ref = None
    status_from, profile_from = await Misc.post_tg_user(
        tg_user_sender,
        did_bot_start=callback.message.chat.type == ChatType.PRIVATE
    )
    if status_from != 200:
        return
    if number == -2:
        # Сообщение участникам
        await state.set_state(FSMsendMessageToOffer.ask)
        await state.update_data(
            uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
        )
        await callback.message.reply(
            (
                'Отправьте или перешлите мне <b>текстовое</b> сообщение для отправки '
                'всем проголосовавшим участникам, кроме недоверенных. '
                'Чтобы не получить недоверия - пишите только по делу!'
            ),
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        await callback.answer()
        return
    if number == -5:
        await state.set_state(FSMOfferPutPlace.ask)
        await state.update_data(
            uuid=profile_from['uuid'],
            offer_uuid=offer_uuid,
        )
        await callback.message.reply(
            Offer.PROMPT_OFFER_GEO,
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        await callback.answer()
        return

    if number == -6:
        status_offer, response_offer = await Offer.post_offer_answer(offer_uuid, profile_from, [-1])
        if status_offer == 200:
            offer = response_offer['offer']
            if offer['desc']:
                if profile_from['username'] == offer['owner']['username']:
                    await callback.message.reply(
                        '\u2193\u2193\u2193 Текущее описание \u2193\u2193\u2193',
                    )
                payload_send_pack = dict(
                    tg_token=settings.TOKEN,
                    messages=offer['desc'],
                    username=profile_from['username'],
                    what='tgdesc',
                )
                # Api пошлёт всем
                status_send_pack, response_send_pack = await Misc.api_request(
                    path='/api/show_tgmsg_pack',
                    method='post',
                    json=payload_send_pack,
                )
            else:
                await callback.message.reply(
                    'Опрос не имеет описания',
                )

            if profile_from['username'] == offer['owner']['username']:
                await state.set_state(FSMofferPutDesc.ask)
                await state.update_data(
                    username=profile_from['username'],
                    offer=offer,
                    uuid_pack=str(uuid4()),
                )
                await callback.message.reply(
                    'Отправьте мне в одном сообщении - фото/видео/текстовое описание опроса',
                    reply_markup=Misc.reply_markup_cancel_row(),
                )
        await callback.answer()
        return

    status_answer, response_answer = await Offer.post_offer_answer(
        offer_uuid, profile_from, [number],
        username_ref=username_ref,
    )
    if status_answer == 200:
        offer = response_answer['offer']
        offer_uuid, username_href = Offer.get_data_from_offer_message(callback.message)
        profile_ref = None
        if username_ref == profile_from['username']:
            profile_ref = profile_from
        elif username_ref:
            status_ref, profile_ref = await Misc.get_user_by_sid(username_ref)
            if status_ref != 200:
                profile_ref = None
        text = Offer.text_offer(
            profile_from, offer, callback.message,
            username_href=username_href,
            profile_ref=profile_ref,
        )
        reply_markup = Offer.markup_offer(
            profile_from, offer, callback.message,
            username_href=username_href,
            profile_ref=profile_ref,
        )
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest:
            pass
        success_message = ''
        if number > 0:
            if offer['closed_timestamp']:
                success_message = 'Владелец остановил голосование'
            else:
                if offer['is_multi']:
                    num_answers = offer['user_answered'][str(profile_from['user_id'])]['answers']
                    success_message = 'Вы выбрали вариант%s:\n' % ('ы' if len(num_answers) > 1 else '')
                    answers_text = '\n'.join([' ' + offer['answers'][n]['answer'] for n in num_answers])
                    success_message += answers_text
                else:
                    success_message = 'Вы выбрали вариант: %s' % offer['answers'][number]['answer']
        elif number == 0:
            if offer['closed_timestamp']:
                success_message = 'Владелец остановил голосование'
            else:
                success_message = 'Вы отозвали свой выбор'
        elif number == -3 and callback.message.chat.type == ChatType.PRIVATE:
            success_message = 'Опрос остановлен'
        elif number == -4 and callback.message.chat.type == ChatType.PRIVATE:
            success_message = 'Опрос возобновлен'
        if success_message:
            await callback.answer(success_message, show_alert=True,)

            if response_answer.get('donate') and response_answer.get('journal_id') and username_ref:
                donate_to = response_answer['donate']
                if donate_to['is_author']:
                    whom = 'автору системы '
                else:
                    whom = 'пригласившей Вас ' if donate_to['profile']['gender'] == 'f' else 'пригласившему Вас '
                whom += Misc.get_deeplink_with_name(donate_to['profile'])

                callback_data_dict = dict(
                    keyboard_type=KeyboardType.DONATE_OFFER_CHOICE,
                    id_=response_answer['journal_id'],
                    donate_to_username=donate_to['profile']['username'],
                    offer_id=offer['offer_id'],
                    username_ref=username_ref or '',
                    sep=KeyboardType.SEP,
                )
                callback_data_template=(
                    f'{Misc.CALLBACK_DATA_ID__TEMPLATE}'
                    '%(donate_to_username)s%(sep)s'
                    '%(username_ref)s%(sep)s'
                    '%(offer_id)s'
                )
                inline_btn_donate = InlineKeyboardButton(
                    text='Сделать дар',
                    callback_data=callback_data_template % callback_data_dict
                )

                callback_data_dict.update(
                    keyboard_type=KeyboardType.DONATE_OFFER_REVOKE_VOICE,
                    id_=offer['offer_id'],
                    message_id=callback.message.message_id,
                    username_href=username_href or ''
                )
                callback_data_template =(
                    f'{Misc.CALLBACK_DATA_ID__TEMPLATE}'
                    '%(message_id)s%(sep)s'
                    '%(username_href)s%(sep)s'
                    '%(username_ref)s%(sep)s'
                )
                inline_btn_revoke_voice = InlineKeyboardButton(
                    text='Отменить голос',
                    callback_data=callback_data_template % callback_data_dict
                )

                await callback.message.reply(
                    f'Предлагаем подкрепить Ваш голос - добровольным даром - {whom}',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            inline_btn_donate,
                            Misc.inline_button_cancel(
                                'Без дара', reply_code='offer_donate')
                        ],
                        [inline_btn_revoke_voice],
                ]))

    elif callback.message.chat.type == ChatType.PRIVATE:
        if number > 0:
            err_mes = 'Не далось подать голос'
        elif number == 0:
            err_mes = 'Не удалось отозвать голос'
        elif number == -1:
            err_mes = 'Не удалось обновить'
        elif number == -3:
            err_mes = 'Не удалось приостановить опрос'
        elif number == -4:
            err_mes = 'Не удалось возобновить опрос'
        else:
            err_mes = 'Ошибка выполнения запроса'
        await callback.message.reply(err_mes)
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMofferPutDesc.ask))
async def process_existing_offer_desc(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if data.get('username') and data.get('offer') and \
       profile_from['username'] == data['username'] and \
       data.get('offer', {}).get('owner', {}).get('username') and \
       data['offer']['owner']['username'] == data['username'] and \
       data.get('uuid_pack'):
        key = (
            f'{Rcache.OFFER_DESC_PREFIX}{Rcache.KEY_SEP}'
            f'{data["uuid_pack"]}'
        )
        if await Misc.check_none_n_clear(is_first := Misc.redis_is_key_first_up(key), state):
            status, response = await Offer.put_offer_properties(
                username=data['username'],
                offer_uuid=data['offer']['uuid'],
                is_first=is_first,
                tgdesc=TgDesc.from_message(message, data['uuid_pack'])
            )
            if not is_first:
                return
            if not await Misc.check_none_n_clear(await Misc.redis_wait_last_in_pack(key), state):
                return
            await message.reply('Описание сохранено')
    await state.clear()


@router.message(F.text, F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMOfferPutPlace.ask))
async def process_existing_offer_location(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if data.get('uuid') and data.get('offer_uuid') and \
       profile_from['uuid'] == data['uuid']:
        latitude, longitude = Misc.check_location_str(message.text)
        if latitude is None or longitude is None:
            error_message = Misc.MSG_ERR_GEO + '\n\n' + Offer.PROMPT_OFFER_GEO
            await message.reply(
                error_message,
                reply_markup=Misc.reply_markup_cancel_row(),
            )
            return
    status_answer, response_answer = await Offer.post_offer_answer(
        data['offer_uuid'],
        profile_from,
        [-5],
        latitude=latitude, longitude=longitude,
    )
    if status_answer == 200:
        reply = f'Координаты опроса установлены'
    else:
        reply = Misc.MSG_ERROR_API
    await message.reply(reply, disable_notification=True)
    await state.clear()


@router.message(F.text, F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMsendMessageToOffer.ask))
async def process_message_to_offer(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    state_finished = False
    data = await state.get_data()
    if data.get('uuid') and data.get('offer_uuid'):
        status_sender, response_sender = await Misc.post_tg_user(message.from_user)
        if status_sender == 200 and response_sender.get('uuid') == data['uuid']:
            payload = dict(
                tg_token=settings.TOKEN,
                user_uuid=data['uuid'],
                offer_uuid=data['offer_uuid']
            )
            logging.debug('/api/offer/voted/tg_users %s' % Misc.secret(payload ))
            status, response = await Misc.api_request(
                path='/api/offer/voted/tg_users',
                method='post',
                json=payload,
            )
            logging.debug('/api/offer/voted/tg_users, status: %s' % status)
            logging.debug('/api/offer/voted/tg_users: %s' % response)
            if status == 200:
                n_delivered = 0
                if response['users']:
                    msg_to = (
                            'Сообщение участникам опроса:\n'
                            '\n'
                            '%(offer_deeplink)s\n'
                            '\n'
                            'от %(sender_deeplink)s\n'
                            '\n'
                            '\u2193\u2193\u2193'
                        ) % dict(
                        offer_deeplink=Misc.get_html_a(
                            # ниже: username_href=None, при открытии ссылки username_ref будет владелец опроса,
                            # он же попадет в реферер
                            href=Offer.get_deeplink(data["offer_uuid"], username_href=None),
                            text=response['question'],
                        ),
                        sender_deeplink=Misc.get_deeplink_with_name(response_sender)
                    )
                    await state.clear()
                    state_finished = True
                    for user in response['users']:
                        delivered_to_user = False
                        for tg_account in user['tg_data']:
                            tg_uid = tg_account['tg_uid']
                            try:
                                await bot.send_message(tg_uid, text=msg_to)
                                await bot.copy_message(
                                    tg_uid,
                                    from_chat_id=message.chat.id,
                                    message_id=message.message_id,
                                )
                                delivered_to_user = True
                            except (TelegramBadRequest, TelegramForbiddenError,):
                                pass
                        if delivered_to_user:
                            n_delivered += 1
                if n_delivered == 0:
                    msg = 'Сообщение никому не отправлено'
                else:
                    msg = 'Сообщение отправлено %s %s' % (
                        n_delivered,
                        'адресату' if n_delivered == 1 else 'адресатам',
                    )
                await message.reply(msg)
            else:
                await message.reply('Опрос не найден или вы не его ваделец')
    if not state_finished:
        await state.clear()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.DONATE_OFFER_CHOICE,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_donate_office_choice(callback: CallbackQuery, state: FSMContext):
    try:
        split = callback.data.split(KeyboardType.SEP)
        journal_id = int(split[1])
        donate_to_username=split[2]
        username_ref=split[3]
        offer_id=split[4]
    except (TypeError, ValueError, IndexError,):
        await callback.answer(); return
    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await callback.answer(); return
    status_to, profile_to = await Misc.get_user_by_sid(donate_to_username)
    if status_to != 200:
        await callback.answer(); return
    bank_details = await Misc.get_bank_details(profile_to['uuid'])
    if bank_details:
        status_offer, response_offer = await Offer.get_offer(offer_id=offer_id, user_ids_only='on')
        if status_offer == 200:
            offer = response_offer['offer']
            text_after_thank = (
                'Пришлите мне снимок экрана добровольного дара любой суммы — '
                'в качестве подкрепления Вашего голоса — на Реквизиты платежей ниже.\n'
                'В сообщение можно добавить фото/видео/текстовый комментарий.\n'
                'При отмене голоса дар не возвращается.\n'
                '\n'
                f'{html.quote(bank_details)}\n\n'
            )
            try:
                await state.set_state(FSMofferChoiceDonate.ask)
                await state.update_data(
                    profile_to=profile_to,
                    profile_from=profile_from,
                    journal_id=journal_id,
                    uuid_pack=str(uuid4()),
                    username_ref=username_ref,
                    offer_uuid=response_offer['offer']['uuid'],
                )
                await bot.send_message(
                    callback.from_user.id,
                    text=text_after_thank,
                    reply_markup=Misc.reply_markup_cancel_row(),
                )
            except (TelegramBadRequest, TelegramForbiddenError,):
                pass
        else:
            await callback.message.reply('Опрос не найден')
    else:
        await callback.message.reply(f'{profile_to["first_name"]} не имеет банковских реквизитов')
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMofferChoiceDonate.ask))
async def process_message_thank_office_choice(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    if not (profile_to := data.get('profile_to')) or not (journal_id := data.get('journal_id')):
        await state.clear(); return
    status_from, profile_from = await Misc.post_tg_user(message.from_user)
    if status_from != 200 or profile_from['uuid'] != data.get('profile_from', {}).get('uuid', ''):
        await state.clear(); return
    key = (
        f'{Rcache.DONATE_OFFER_CHOICE}{Rcache.KEY_SEP}'
        f'{data["uuid_pack"]}'
    )
    if not await Misc.check_none_n_clear(is_first := Misc.redis_is_key_first_up(key), state):
        return
    tgdesc_payload  = dict(
        tg_token=settings.TOKEN,
        journal_id=journal_id,
        is_first=is_first,
    )
    tgdesc_payload.update(tgdesc=TgDesc.from_message(message, data['uuid_pack']))
    logging.debug('post donate offer, payload: %s' % Misc.secret(tgdesc_payload))
    status, response = await Misc.api_request(
        '/api/thank_bank',
        method='POST',
        json = tgdesc_payload
    )
    logging.debug('post donate offer, status: %s' % status)
    logging.debug('post donate offer, response: %s' % response)
    if status == 200:
        if not is_first:
            return
        if not await Misc.check_none_n_clear(await Misc.redis_wait_last_in_pack(key), state):
            return

        offer_link = Misc.get_html_a(
            Offer.get_deeplink(data['offer_uuid'], data['username_ref']),
            'опрос',
        )
        text = (
            f'Вам поступил добровольный дар от '
            f'{Misc.get_deeplink_with_name(profile_from)} за {offer_link}'
            '\n'
            '\u2193\u2193\u2193'
        )
        for tg_account in data['profile_to']['tg_data']:
            try:
                await bot.send_message(tg_account['tg_uid'], text=text)
            except (TelegramBadRequest, TelegramForbiddenError,):
                pass

        payload_send_pack = dict(
            tg_token=settings.TOKEN,
            uuid_pack=data['uuid_pack'],
            username=profile_to['username'],
            what='tgdesc',
        )
        # Api пошлёт всем
        status_send_pack, response_send_pack = await Misc.api_request(
            path='/api/show_tgmsg_pack',
            method='post',
            json=payload_send_pack,
        )
        await message.reply(
            'Сообщение передано получателю' if status_send_pack == 200 else \
            'Получатель не принял сообщение'
        )
    await state.clear()

@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.DONATE_OFFER_REVOKE_VOICE,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_donate_office_choice(callback: CallbackQuery, state: FSMContext):
    try:
        split = callback.data.split(KeyboardType.SEP)
        offer_id = split[1]
        message_id = split[2]
        username_href = split[3]
        username_ref = split[4]
    except (TypeError, ValueError, IndexError,):
        await callback.answer(); return

    status_from, profile_from = await Misc.post_tg_user(callback.from_user)
    if status_from != 200:
        await callback.answer(); return

    status_offer, response_offer = await Offer.get_offer(offer_id=offer_id, user_ids_only='on')
    if status_offer != 200:
        await callback.answer(); return
    offer_uuid = response_offer['offer']['uuid']

    profile_ref = None
    if username_ref == profile_from['username']:
        profile_ref = profile_from
    elif username_ref:
        status_ref, profile_ref = await Misc.get_user_by_sid(username_ref)
        if status_ref != 200:
            profile_ref = None

    status_answer, response_answer = await Offer.post_offer_answer(
        offer_uuid, profile_from, [0],
        username_ref=username_ref,
    )
    if status_answer != 200:
        await callback.answer(); return
    offer = response_answer['offer']

    text = Offer.text_offer(
        profile_from, offer,
        message=None,
        username_href=username_href,
        profile_ref=profile_ref,
    )
    reply_markup = Offer.markup_offer(
        profile_from, offer,
        message=None,
        username_href=username_href,
        profile_ref=profile_ref,
    )
    try:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
    except:
        pass
    await callback.answer('Вы отозвали свой выбор', show_alert=True,)
