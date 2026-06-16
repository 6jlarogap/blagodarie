# handler_offer.py
#
# Команды и сообщения для занесения родственников

import re

from aiogram import Router, F, html
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

from common import Misc, KeyboardType, OperationType, TgGroup, TgGroupMember

import me
dp, bot, bot_data = me.dp, me.bot, me.bot_data

router = Router()

class FSMpapaMama(StatesGroup):
    ask = State()
    new = State()
    confirm_clear = State()

class FSMchild(StatesGroup):
    parent_gender = State()
    ask = State()
    new = State()
    choose = State()
    confirm_clear = State()

class FSMbroSis(StatesGroup):
    ask = State()
    new = State()


@router.callback_query(F.data.regexp(r'^(%s|%s)%s' % (
        KeyboardType.FATHER, KeyboardType.MOTHER,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_papa_mama(callback: CallbackQuery, state: FSMContext):
    """
    Действия по заданию папы, мамы
    """
    code = callback.data.split(KeyboardType.SEP)
    uuid = None
    try:
        uuid = code[1]
    except IndexError:
        pass
    if not uuid:
        await callback.answer()
        return
    tg_user_sender = callback.from_user
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=tg_user_sender, uuid=uuid)
    if not response_sender:
        await callback.answer()
        return
    response_uuid = response_sender['response_uuid']
    is_father = code[0] == str(KeyboardType.FATHER)

    existing_parent = None
    if is_father and response_sender['response_uuid'].get('father'):
        existing_parent = response_sender['response_uuid']['father']
    elif not is_father and response_sender['response_uuid'].get('mother'):
        existing_parent = response_sender['response_uuid']['mother']

    await state.update_data(
        uuid = uuid,
        is_father = is_father,
        existing_parent_uuid = existing_parent['uuid'] if existing_parent else None,
        existing_parent_name = existing_parent['first_name'] if existing_parent else None
    )
    callback_data_new_parent = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
        keyboard_type=KeyboardType.NEW_FATHER if is_father else KeyboardType.NEW_MOTHER,
        uuid=uuid,
        sep=KeyboardType.SEP,
    )
    novy_novaya = 'Новый' if is_father else 'Новая'
    inline_btn_new_papa_mama = InlineKeyboardButton(
        text=novy_novaya,
        callback_data=callback_data_new_parent,
    )
    buttons = [inline_btn_new_papa_mama, ]
    if existing_parent:
        callback_data_clear_parent = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
            keyboard_type=KeyboardType.CLEAR_PARENT,
            uuid=uuid,
            sep=KeyboardType.SEP,
        )
        inline_btn_clear_parent = InlineKeyboardButton(
            text='Очистить',
            callback_data=callback_data_clear_parent,
        )
        buttons.append(inline_btn_clear_parent)
    prompt_papa_mama = (
        'Отправьте мне <u><b>ссылку на профиль %(papy_or_mamy)s</b></u> для '
        '%(response_uuid_name)s '
        'вида t.me/%(bot_data_username)s?start=...\n'
        '\n'
        'Или нажмите <b><u>%(novy_novaya)s</u></b> - для нового профиля %(papy_or_mamy)s\n'
    )
    if existing_parent:
        prompt_papa_mama += (
            '\n'
            'Или нажмите <b><u>Очистить</u></b> - для очистки имеющейся родственной связи: '
            '<b>%(existing_parent_name)s</b> - %(papa_or_mama)s для <b>%(response_uuid_name)s</b>'
        )
    prompt_papa_mama = prompt_papa_mama % dict(
        papa_or_mama='папа' if is_father else 'мама',
        papy_or_mamy='папы' if is_father else 'мамы',
        bot_data_username=bot_data.username,
        response_uuid_name=response_sender['response_uuid']['first_name'],
        existing_parent_name=existing_parent['first_name'] if existing_parent else '',
        novy_novaya=novy_novaya,
    )
    buttons.append(Misc.inline_button_cancel())
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[ buttons ])
    await state.set_state(FSMpapaMama.ask)
    await callback.message.reply(
        prompt_papa_mama,
        reply_markup=reply_markup,
    )
    await callback.answer()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.CLEAR_PARENT,
        KeyboardType.SEP,
    )), StateFilter(FSMpapaMama.ask))
async def cbq_callback_clear_parent(callback: CallbackQuery, state: FSMContext):
    """
    Действия по обнулению папы, мамы
    """
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear(); await callback.answer()
        return
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response_sender:
        await state.clear(); await callback.answer()
        return
    data = await state.get_data()
    if not data.get('existing_parent_uuid') or \
        ('is_father' not in data) or \
        not data.get('existing_parent_name') or \
        data.get('uuid') != uuid:
        await state.clear(); await callback.answer()
        return
    existing_parent_name = data['existing_parent_name']
    is_father = data['is_father']
    prompt = (
        'Вы уверены, что хотите очистить родственную связь: '
        '<b>%(existing_parent_name)s</b> - %(papa_or_mama)s для <b>%(response_uuid_name)s</b>?\n\n'
        'Если уверены, нажмите <b><u>Очистить</u></b>'
        ) % dict(
        papa_or_mama='папа' if is_father else 'мама',
        response_uuid_name=response_sender['response_uuid']['first_name'],
        existing_parent_name=existing_parent_name,
    )
    callback_data_clear_parent_confirm = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
        keyboard_type=KeyboardType.CLEAR_PARENT_CONFIRM,
        uuid=uuid,
        sep=KeyboardType.SEP,
    )
    inline_btn_clear_parent_confirm = InlineKeyboardButton(
        text='Очистить',
        callback_data=callback_data_clear_parent_confirm,
    )
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
        inline_btn_clear_parent_confirm, Misc.inline_button_cancel()
    ]])
    await state.set_state(FSMpapaMama.confirm_clear)
    await callback.message.reply(
        prompt,
        reply_markup=reply_markup,
    )
    await callback.answer()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.CLEAR_PARENT_CONFIRM,
        KeyboardType.SEP,
    )), StateFilter(FSMpapaMama.confirm_clear))
async def cbq_callback_clear_parent_confirmed(callback: CallbackQuery, state: FSMContext):
    """
    Действия по обнулению папы, мамы
    """
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear(); await callback.answer()
        return
    message = callback.message
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response_sender:
        await state.clear(); await callback.answer()
        return
    data = await state.get_data()
    if not data.get('existing_parent_uuid') or \
       ('is_father' not in data) or \
       not data.get('existing_parent_name') or \
       data.get('uuid') != uuid:
        await state.clear(); await callback.answer()
        return
    existing_parent_uuid = data['existing_parent_uuid']
    is_father = data['is_father']
    post_op = dict(
        tg_token=settings.TOKEN,
        operation_type_id=OperationType.NOT_PARENT,
        user_id_from=response_sender['response_uuid']['uuid'],
        user_id_to=existing_parent_uuid,
    )
    logging.debug('post operation, payload: %s' % Misc.secret(post_op))
    status, response = await Misc.api_request(
        path='/api/addoperation',
        method='post',
        data=post_op,
    )
    logging.debug('post operation, status: %s' % status)
    logging.debug('post operation, response: %s' % response)
    if not (status == 200 or \
       status == 400 and response.get('code') == 'already'):
        if status == 400  and response.get('message'):
            await message.reply(
                'Ошибка!\n%s\n\nОчищайте родителя по новой' % response['message']
            )
        else:
            await message.reply(Misc.MSG_ERROR_API)
    else:
        if response and response.get('profile_from') and response.get('profile_to'):
            await bot.send_message(
                callback.from_user.id,
                Misc.PROMPT_PAPA_MAMA_CLEARED % dict(
                    iof_from = Misc.get_deeplink_with_name(response['profile_from'], plus_trusts=True),
                    iof_to = Misc.get_deeplink_with_name(response['profile_to'], plus_trusts=True),
                    papa_or_mama='папа' if is_father else 'мама',
            ))
        else:
            await message.reply('Связь Ребенок - Родитель очищена')
    await state.clear()
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMpapaMama.ask))
async def put_papa_mama(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    user_sid_to = Misc.sid_from_link(message.text)
    if not user_sid_to:
        if await is_it_command(message, state, excepts=('start',)):
            return
        data = await state.get_data()
        uuid = data.get('uuid')
        is_father = data.get('is_father')
        if uuid and is_father is not None:
            if is_father:
                prompt_new_parent = 'Новый'
            else:
                prompt_new_parent = 'Новая'
            msg_invalid_link_with_new = (
                f'Профиль не найден - попробуйте скопировать и отправить ссылку '
                f'на существующий профиль ещё раз или создайте '
                f'<u>{prompt_new_parent}</u>'
            )
            button_new_parent = InlineKeyboardButton(
                text=prompt_new_parent,
                callback_data= Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
                    keyboard_type=KeyboardType.NEW_FATHER if is_father else KeyboardType.NEW_MOTHER,
                    uuid=uuid,
                    sep=KeyboardType.SEP,
            ))
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                button_new_parent, Misc.inline_button_cancel()
            ]])
            await message.reply(
                msg_invalid_link_with_new,
                reply_markup=reply_markup
            )
        else:
            await message.reply(
                Misc.MSG_INVALID_LINK + '\nПовторите, пожалуйста' ,
                reply_markup=Misc.reply_markup_cancel_row()
            )
        return
    user_uuid_from = is_father = ''
    data = await state.get_data()
    if data.get('uuid'):
        user_uuid_from = data['uuid']
        is_father = data.get('is_father')
    if not user_uuid_from or not isinstance(is_father, bool):
        await state.clear()
        return
    response_sender = await Misc.check_owner_by_sid(owner_tg_user=message.from_user, sid=user_sid_to)
    if not response_sender:
        await state.clear()
        return

    post_op = dict(
        tg_token=settings.TOKEN,
        operation_type_id=OperationType.SET_FATHER if is_father else OperationType.SET_MOTHER,
        user_id_from=user_uuid_from,
        user_id_to=response_sender['response_uuid']['uuid']
    )
    logging.debug('post operation, payload: %s' % Misc.secret(post_op))
    status, response = await Misc.api_request(
        path='/api/addoperation',
        method='post',
        data=post_op,
    )
    logging.debug('post operation, status: %s' % status)
    logging.debug('post operation, response: %s' % response)
    if not (status == 200 or \
           status == 400 and response.get('code') == 'already'):
        if status == 400  and response.get('message'):
            await message.reply(
                'Ошибка!\n%s\n\nНазначайте родителя по новой' % response['message']
            )
        else:
            await message.reply(Misc.MSG_ERROR_API)
    else:
        if response and response.get('profile_from') and response.get('profile_to'):
            if not response['profile_to'].get('gender'):
                await Misc.put_user_properties(
                    uuid=response['profile_to']['uuid'],
                    gender='m' if is_father else 'f',
                )
            await bot.send_message(
                message.from_user.id,
                Misc.PROMPT_PAPA_MAMA_SET % dict(
                    iof_from = Misc.get_deeplink_with_name(response['profile_from'], plus_trusts=True),
                    iof_to = Misc.get_deeplink_with_name(response['profile_to'], plus_trusts=True),
                    papa_or_mama='папа' if is_father else 'мама',
                    _a_='' if is_father else 'а',
                ))
        else:
            await message.reply('Родитель внесен в данные')
    await state.clear()

@router.callback_query(F.data.regexp(r'^(%s|%s)%s' % (
        KeyboardType.NEW_FATHER, KeyboardType.NEW_MOTHER,
        KeyboardType.SEP,
    )), StateFilter(FSMpapaMama.ask))
async def cbq_new_papa_mama(callback: CallbackQuery, state: FSMContext):
    """
    Действия по заданию папы, мамы
    """
    tg_user_sender = callback.from_user
    code = callback.data.split(KeyboardType.SEP)
    uuid = None
    try:
        uuid = code[1]
    except IndexError:
        pass
    if not uuid:
        await state.clear(); await callback.answer()
        return
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=tg_user_sender, uuid=uuid)
    if not response_sender:
        await state.clear(); await callback.answer()
        return
    is_father = code[0] == str(KeyboardType.NEW_FATHER)
    response_uuid = response_sender['response_uuid']
    prompt_new_papa_mama = (
        'Укажите Имя Фамилию и Отчество для %(papy_or_mamy)s, '
        'пример %(fio_pama_mama)s'
    ) % dict(
        papy_or_mamy='папы' if is_father else 'мамы',
        name=Misc.get_deeplink_with_name(response_uuid, plus_trusts=True),
        fio_pama_mama='Иван Иванович Иванов'if is_father else 'Марья Ивановна Иванова',
    )
    await state.set_state(FSMpapaMama.new)
    await state.update_data(uuid=uuid, is_father=is_father)
    await callback.message.reply(
        prompt_new_papa_mama,
        reply_markup=Misc.reply_markup_cancel_row(),
    )
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMpapaMama.new))
async def put_new_papa_mama(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    if await is_it_command(message, state):
        return
    first_name_to = Misc.strip_text(message.text)
    user_uuid_from = is_father = ''
    data = await state.get_data()
    if data.get('uuid'):
        user_uuid_from = data['uuid']
        is_father = data.get('is_father')
    if not user_uuid_from or not isinstance(is_father, bool):
        await state.clear()
        return
    owner = await Misc.check_owner_by_uuid(owner_tg_user=message.from_user, uuid=user_uuid_from)
    if not owner or not owner.get('user_id'):
        await state.clear()
        return

    post_data = dict(
        tg_token=settings.TOKEN,
        first_name = first_name_to,
        link_relation='new_is_father' if is_father else 'new_is_mother',
        link_id=user_uuid_from,
        owner_id=owner['user_id'],
    )
    logging.debug('post new owned user with link_id, payload: %s' % Misc.secret(post_data))
    status, response = await Misc.api_request(
        path='/api/profile',
        method='post',
        data=post_data,
    )
    logging.debug('post new owned user with link_id, status: %s' % status)
    logging.debug('post new owned user with link_id, response: %s' % response)
    if status != 200:
        if status == 400  and response.get('message'):
            await message.reply(
                'Ошибка!\n%s\n\nНазначайте родителя по новой' % response['message']
            )
        else:
            await message.reply(Misc.MSG_ERROR_API)
    else:
        if response and response.get('profile_from'):
            await Misc.put_user_properties(
                uuid=response['uuid'],
                gender='m' if is_father else 'f',
            )
            await bot.send_message(
                message.from_user.id,
                Misc.PROMPT_PAPA_MAMA_SET % dict(
                iof_from = Misc.get_deeplink_with_name(response['profile_from'], plus_trusts=True),
                iof_to = Misc.get_deeplink_with_name(response, plus_trusts=True),
                papa_or_mama='папа' if is_father else 'мама',
                _a_='' if is_father else 'а',
                ))
            await Misc.show_card(
                profile=response,
                profile_sender=owner,
                tg_user_sender=message.from_user,
            )
        else:
            await message.reply('Родитель внесен в данные')
    await state.clear()

@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.CHILD,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_callback_child(callback: CallbackQuery, state: FSMContext):
    """
    Действия по заданию сына, дочери
    """
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        return
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response_sender:
        return
    response_uuid = response_sender['response_uuid']
    reply_markup = None
    await state.update_data(uuid=uuid, name=response_uuid['first_name'])
    if response_uuid['gender']:
        await state.update_data(parent_gender=response_uuid['gender'])
        await ask_child(callback.message, state, children=response_sender['response_uuid']['children'])
    else:
        await state.update_data(parent_gender=None)
        callback_data = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
            keyboard_type=KeyboardType.FATHER_OF_CHILD,
            uuid=uuid,
            sep=KeyboardType.SEP,
        )
        inline_btn_papa_of_child = InlineKeyboardButton(
            text='Муж',
            callback_data=callback_data,
        )
        callback_data = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
            keyboard_type=KeyboardType.MOTHER_OF_CHILD,
            uuid=uuid,
            sep=KeyboardType.SEP,
        )
        inline_btn_mama_of_child = InlineKeyboardButton(
            text='Жен',
            callback_data=callback_data,
        )
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
            inline_btn_papa_of_child, inline_btn_mama_of_child, Misc.inline_button_cancel()
        ]])
        prompt_papa_mama_of_child = Misc.PROMPT_PAPA_MAMA_OF_CHILD % dict(
            name=response_uuid['first_name'],
        )
        await FSMchild.parent_gender.set()
        await callback.message.reply(
            prompt_papa_mama_of_child,
            reply_markup=reply_markup,
        )
    await callback.answer()

async def ask_child(message, state, children):
    data = await state.get_data()
    prompt_child = (
        '<b>%(name)s</b>.\n'
        'Отправьте мне <u><b>ссылку на профиль %(his_her)s сына (дочери)</b></u> '
        'вида t.me/%(bot_data_username)s?start=...\n'
        '\n'
        'Или нажмите <b><u>Новый сын</u></b> или <b><u>Новая дочь</u></b> для ввода нового родственника, '
        'который станет %(his_her)s сыном или дочерью\n'
    )
    if children:
        if len(children) == 1:
            prompt_child += (
                '\n'
                'Или нажмите <b><u>Очистить</u></b> для очистки %(his_her)s родственной связи '
                'с <b>%(name_of_single_child)s</b>\n'
            )
        else:
            prompt_child += (
                '\n'
                'Или нажмите <b><u>Очистить</u></b> для очистки родственной связи '
                'с кем-то из %(his_her)s детей\n'
            )
    prompt_child = prompt_child % dict(
        bot_data_username=bot_data.username,
        name=data['name'],
        his_her='его' if data['parent_gender'] == 'm' else 'её',
        name_of_single_child=children[0]['first_name'] if children else '',
    )
    data_new_child = dict(
        keyboard_type=KeyboardType.NEW_SON,
        uuid=data['uuid'],
        sep=KeyboardType.SEP,
    )
    inline_btn_new_son = InlineKeyboardButton(
        text='Новый сын',
        callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % data_new_child,
    )
    data_new_child.update(keyboard_type=KeyboardType.NEW_DAUGHTER)
    inline_btn_new_daughter = InlineKeyboardButton(
        text='Новая дочь',
        callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % data_new_child,
    )
    buttons = [inline_btn_new_son, inline_btn_new_daughter, ]
    if children:
        callback_data_clear_child = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
            keyboard_type=KeyboardType.CLEAR_CHILD,
            uuid=data['uuid'],
            sep=KeyboardType.SEP,
        )
        inline_btn_clear_child = InlineKeyboardButton(
            text='Очистить',
            callback_data=callback_data_clear_child,
        )
        buttons.append(inline_btn_clear_child)
    buttons.append(Misc.inline_button_cancel())
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[ buttons ])
    await state.set_state(FSMchild.ask)
    await message.reply(
        prompt_child,
        reply_markup=reply_markup,
    )


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.CLEAR_CHILD,
        KeyboardType.SEP,
    )), StateFilter(FSMchild.ask))
async def cbq_clear_child(callback: CallbackQuery, state: FSMContext):
    """
    Действия по вопросу об обнулении ребенка
    """
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear()
        return
    message = callback.message
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response_sender or \
       not response_sender.get('response_uuid') or \
       not response_sender['response_uuid'].get('children'):
        await state.clear()
        return
    data = await state.get_data()
    if not data or \
       not data.get('parent_gender') or \
       data.get('uuid') != uuid:
        await state.clear()
        return
    parent = response_sender['response_uuid']
    children = parent['children']
    if len(children) == 1:
        await clear_child_confirm(children[0], parent, callback.message, state)
    else:
        prompt = (
            'У <b>%(parent_name)s</b> несколько детей. Нажмите на ссылку того, '
            'с кем собираетесь разорвать %(his_her)s родственную связь\n\n'
        )
        prompt = prompt % dict(
            parent_name=html.quote(parent['first_name']),
            his_her='его' if data['parent_gender'] == 'm' else 'её',
        )
        for child in children:
            prompt += Misc.get_deeplink_with_name(child, plus_trusts=True) + '\n'
        await state.set_state(FSMchild.choose)
        await callback.message.reply(
            prompt,
            reply_markup=Misc.reply_markup_cancel_row(),
        )
    await callback.answer()


async def clear_child_confirm(child_profile, parent_profile, message, state):
    """
    Подтвердить очистить связь родитель -> ребенок
    """
    data = await state.get_data()
    if not data or not data.get('parent_gender') or not data.get('uuid'):
        await state.clear()
        return
    prompt = (
        'Вы уверены, что хотите очистить родственную связь: '
        '<b>%(parent_name)s</b> - %(papa_or_mama)s для <b>%(child_name)s</b>?\n\n'
        'Если уверены, нажмите <b><u>Очистить</u></b>'
        ) % dict(
        papa_or_mama='папа' if data['parent_gender'] == 'm' else 'мама',
        parent_name=html.quote(parent_profile['first_name']),
        child_name=html.quote(child_profile['first_name']),
    )
    callback_data_clear_child_confirm = Misc.CALLBACK_DATA_UUID_TEMPLATE % dict(
        keyboard_type=KeyboardType.CLEAR_CHILD_CONFIRM,
        uuid=parent_profile['uuid'],
        sep=KeyboardType.SEP,
    )
    inline_btn_clear_child_confirm = InlineKeyboardButton(
        text='Очистить',
        callback_data=callback_data_clear_child_confirm,
    )
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
        inline_btn_clear_child_confirm, Misc.inline_button_cancel()
    ]])
    await state.update_data(child_uuid = child_profile['uuid'])
    await state.set_state(FSMchild.confirm_clear)
    await message.reply(
        prompt,
        reply_markup=reply_markup,
    )


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMchild.choose))
async def choose_child_to_clear_link(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_INVALID_LINK + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    if await is_it_command(message, state, excepts=('start',)):
        return
    child_sid = Misc.sid_from_link(message.text)
    if not child_sid:
        await message.reply(
            Misc.MSG_INVALID_LINK + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    data = await state.get_data()
    if data.get('uuid') and data.get('parent_gender'):
        parent_uuid = data['uuid']
        response_sender = await Misc.check_owner_by_uuid(owner_tg_user=message.from_user, uuid=parent_uuid)
        if not response_sender:
            await state.clear()
            return
        parent_profile = response_sender['response_uuid']
        children = parent_profile.get('children', [])
        child_profile = None
        for child in children:
            if child['username'] == child_sid:
                child_profile = child
                break
        if not child_profile:
            await message.reply(
                'Это ссылка на кого-то другого, а не на одного из детей <b>%s</b>\n\n%s' % (
                    html.quote(parent_profile['first_name']),
                    Misc.MSG_REPEATE_PLEASE,
                ),
                reply_markup=Misc.reply_markup_cancel_row()
            )
            return
        await clear_child_confirm(child_profile, parent_profile, message, state)
    else:
        await state.clear()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.CLEAR_CHILD_CONFIRM,
        KeyboardType.SEP,
    )), StateFilter(FSMchild.confirm_clear))
async def cbq_clear_child_confirmed(callback: CallbackQuery, state: FSMContext):
    """
    Действия по вопросу об обнулении ребенка
    """
    if not (parent_uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear(); await callback.answer()
        return
    message = callback.message
    tg_user_sender = callback.from_user
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=tg_user_sender, uuid=parent_uuid)
    if not response_sender or \
       not response_sender.get('response_uuid') or \
       not response_sender['response_uuid'].get('children'):
        await state.clear(); await callback.answer()
        return
    data = await state.get_data()
    if not data or \
       not data.get('parent_gender') or \
       data.get('uuid') != parent_uuid or \
       not data.get('child_uuid'):
        await state.clear(); await callback.answer()
        return
    is_father = data['parent_gender'] == 'm'
    post_op = dict(
        tg_token=settings.TOKEN,
        operation_type_id=OperationType.NOT_PARENT,
        user_id_from=data['child_uuid'],
        user_id_to=parent_uuid,
    )
    logging.debug('post operation, payload: %s' % Misc.secret(post_op))
    status, response = await Misc.api_request(
        path='/api/addoperation',
        method='post',
        data=post_op,
    )
    logging.debug('post operation, status: %s' % status)
    logging.debug('post operation, response: %s' % response)
    if not (status == 200 or \
       status == 400 and response.get('code') == 'already'):
        if status == 400  and response.get('message'):
            await message.reply(
                'Ошибка!\n%s\n\nОчищайте ребенка по новой' % response['message']
            )
        else:
            await message.reply(Misc.MSG_ERROR_API)
    else:
        if response and response.get('profile_from') and response.get('profile_to'):
            if not response['profile_to']['gender']:
                await Misc.put_user_properties(
                    uuid=response['profile_to']['uuid'],
                    gender='m' if is_father else 'f',
                )
            await bot.send_message(
                tg_user_sender.id,
                Misc.PROMPT_PAPA_MAMA_CLEARED % dict(
                    iof_from = Misc.get_deeplink_with_name(response['profile_from'], plus_trusts=True),
                    iof_to = Misc.get_deeplink_with_name(response['profile_to'], plus_trusts=True),
                    papa_or_mama='папа' if is_father else 'мама',
                ))
        else:
            await message.reply('Связь Родитель - Ребенок очищена')
    await state.clear()
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMchild.ask))
async def put_child_by_sid(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    user_sid_from = Misc.sid_from_link(message.text)
    if not user_sid_from:
        if await is_it_command(message, state, excepts=('start',)):
            return
        data = await state.get_data()
        if uuid := data.get('uuid'):
            data_new_child = dict(
                keyboard_type=KeyboardType.NEW_SON,
                uuid=uuid,
                sep=KeyboardType.SEP,
            )
            inline_btn_new_son = InlineKeyboardButton(
                'Новый сын',
                callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % data_new_child,
            )
            data_new_child.update(keyboard_type=KeyboardType.NEW_DAUGHTER)
            inline_btn_new_daughter = InlineKeyboardButton(
                'Новая дочь',
                callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % data_new_child,
            )
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                inline_btn_new_son, inline_btn_new_daughter, Misc.inline_button_cancel()
            ]])
            await message.reply(
                'Профиль не найден - попробуйте скопировать и отправить ссылку '
                'на существующий профиль ещё раз или создайте <u>Новый сын</u> или <u>Новая дочь</u>',
                reply_markup=reply_markup
            )
        else:
            await message.reply(
                Misc.MSG_INVALID_LINK + '\nПовторите, пожалуйста' ,
                reply_markup=Misc.reply_markup_cancel_row()
            )
        return

    data = await state.get_data()
    if data.get('uuid') and data.get('parent_gender'):
        response_sender = await Misc.check_owner_by_sid(owner_tg_user=message.from_user, sid=user_sid_from)
        if response_sender:
            user_uuid_from = response_sender['response_uuid']['uuid']
            is_father = data['parent_gender'] == 'm'
            post_op = dict(
                tg_token=settings.TOKEN,
                operation_type_id=OperationType.SET_FATHER if is_father else OperationType.SET_MOTHER,
                user_id_from=user_uuid_from,
                user_id_to=data['uuid'],
            )
            logging.debug('post operation, payload: %s' % Misc.secret(post_op))
            status, response = await Misc.api_request(
                path='/api/addoperation',
                method='post',
                data=post_op,
            )
            logging.debug('post operation, status: %s' % status)
            logging.debug('post operation, response: %s' % response)
            if not (status == 200 or \
               status == 400 and response.get('code') == 'already'):
                if status == 400  and response.get('message'):
                    await message.reply(
                        'Ошибка!\n%s\n\nНазначайте ребёнка по новой' % response['message']
                    )
                else:
                    await message.reply(Misc.MSG_ERROR_API)
            else:
                if response and response.get('profile_from') and response.get('profile_to'):
                    if not response['profile_to'].get('gender'):
                        await Misc.put_user_properties(
                            uuid=response['profile_to']['uuid'],
                            gender='m' if is_father else 'f',
                        )
                    await message.reply(Misc.PROMPT_PAPA_MAMA_SET % dict(
                            iof_from = Misc.get_deeplink_with_name(response['profile_from'], plus_trusts=True),
                            iof_to = Misc.get_deeplink_with_name(response['profile_to'], plus_trusts=True),
                            papa_or_mama='папа' if is_father else 'мама',
                            _a_='' if is_father else 'а',
                    ))
                else:
                    await message.reply('Родитель внесен в данные')
        else:
            # Не имеет права
            await message.reply((
                'Нельзя назначать ребенка, если это активный пользователь или профиль, '
                'которым владеете не Вы.\n\n'
                'Назначайте ребёнка по новой'
            ))
    await state.clear()


@router.callback_query(F.data.regexp(r'^(%s|%s)%s' % (
         KeyboardType.NEW_SON, KeyboardType.NEW_DAUGHTER,
        KeyboardType.SEP,
    )), StateFilter(FSMchild.ask))
async def cbq_new_child_ask_fio(callback: CallbackQuery, state: FSMContext):
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear(); await callback.answer()
        return
    data = await state.get_data()
    for key in ('name', 'uuid', 'parent_gender',):
        if not data.get(key) or key == 'uuid' and data[key] != uuid:
            await state.clear()
            return
    new_child_gender = 'm' \
        if callback.data.split(KeyboardType.SEP)[0] == str(KeyboardType.NEW_SON) \
        else 'f'
    fio_new_child = 'Иван Иванович Иванов' if new_child_gender == 'm' else 'Марья Ивановна Иванова'
    await state.update_data(new_child_gender=new_child_gender)
    await state.set_state(FSMchild.new)
    await callback.message.reply(
        (
            f'Укажите ФИО {"СЫНА" if new_child_gender == "m" else "ДОЧЕРИ"} для:\n'
            f'{data["name"]}\nНапример, {fio_new_child}'
        ),
        reply_markup=Misc.reply_markup_cancel_row(),
    )
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMchild.new))
async def put_new_child(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    if data.get('uuid') and data.get('parent_gender') and data.get('new_child_gender'):
        if message.content_type != ContentType.TEXT:
            await message.reply(
                Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
                reply_markup=Misc.reply_markup_cancel_row()
            )
            return
        first_name = Misc.strip_text(message.text)
        response_sender = await Misc.check_owner_by_uuid(owner_tg_user=message.from_user, uuid=data['uuid'])
        if response_sender:
            response_parent = response_sender['response_uuid']
            if not response_parent['gender']:
                await Misc.put_user_properties(
                    uuid=data['uuid'],
                    gender=data['parent_gender'],
                )
            post_new_link = dict(
                tg_token=settings.TOKEN,
                first_name=first_name,
                link_id=data['uuid'],
                link_relation='link_is_father' if data['parent_gender'] == 'm' else 'link_is_mother',
                owner_id=response_sender['user_id'],
                gender=data['new_child_gender']
            )
            logging.debug('post new child, payload: %s' % Misc.secret(post_new_link))
            status_child, response_child = await Misc.api_request(
                path='/api/profile',
                method='post',
                data=post_new_link,
            )
            logging.debug('post new child, status: %s' % status_child)
            logging.debug('post new child, response: %s' % response_child)
            if status_child != 200:
                if status_child == 400  and response_child.get('message'):
                    await message.reply(
                        'Ошибка!\n%s\n\nНазначайте ребёнка по новой' % response_child['message']
                    )
                else:
                    await message.reply(Misc.MSG_ERROR_API)
            else:
                if response_child:
                    is_father = data['parent_gender'] == 'm'
                    await message.reply(Misc.PROMPT_PAPA_MAMA_SET % dict(
                            iof_from = Misc.get_deeplink_with_name(response_child, plus_trusts=True),
                            iof_to = Misc.get_deeplink_with_name(response_parent, plus_trusts=True),
                            papa_or_mama='папа' if is_father else 'мама',
                            _a_='' if is_father else 'а',
                    ))
                    await Misc.show_card(
                        profile=response_child,
                        profile_sender=response_sender,
                        tg_user_sender=message.from_user,
                    )
                else:
                    await message.reply('Ребёнок внесен в данные')
    await state.clear()


@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.BRO_SIS,
        KeyboardType.SEP,
    )), StateFilter(None))
async def cbq_callback_bro_sis(callback: CallbackQuery, state: FSMContext):
    """
    Действия по заданию брата или сестры
    """
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await callback.answer()
        return
    response_sender = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response_sender:
        await callback.answer()
        return
    response_uuid = response_sender['response_uuid']
    if not (response_uuid.get('father') or response_uuid.get('mother')):
        await callback.answer()
        return
    await state.update_data(uuid = uuid)
    prompt_bro_sis = (
        '<b>%(name)s</b>.\n'
        'Отправьте мне <u><b>ссылку на профиль %(his_her)s брата или сестры</b></u> '
        'вида t.me/%(bot_data_username)s?start=...\n'
        '\n'
        'Или нажмите <b><u>Новый брат</u></b> или <b><u>Новая сестра</u></b> для ввода нового родственника, '
        'который станет %(his_her)s братом или сестрой; родители брата (сестры):\n'
    )
    prompt_bro_sis = prompt_bro_sis % dict(
        bot_data_username=bot_data.username,
        name=response_uuid['first_name'],
        his_her=Misc.his_her(response_uuid),
    )
    if response_uuid.get('father'):
        prompt_bro_sis += f'папа: {response_uuid["father"]["first_name"]}\n'
    if response_uuid.get('mother'):
        prompt_bro_sis += f'мама: {response_uuid["mother"]["first_name"]}\n'

    new_bro_sis_dict = dict(
        keyboard_type=KeyboardType.NEW_BRO,
        uuid=uuid,
        sep=KeyboardType.SEP,
    )
    inline_btn_new_bro = InlineKeyboardButton(
        text='Новый брат',
        callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % new_bro_sis_dict,
    )
    new_bro_sis_dict.update(keyboard_type=KeyboardType.NEW_SIS)
    inline_btn_new_sis = InlineKeyboardButton(
        text='Новая сестра',
        callback_data=Misc.CALLBACK_DATA_UUID_TEMPLATE % new_bro_sis_dict,
    )
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
        inline_btn_new_bro, inline_btn_new_sis, Misc.inline_button_cancel()
    ]])
    await state.set_state(FSMbroSis.ask)
    await callback.message.reply(
        prompt_bro_sis,
        reply_markup=reply_markup,
    )
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMbroSis.ask))
async def put_bro_sys_by_sid(message: Message, state: FSMContext):
    if message.content_type != ContentType.TEXT:
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    sid_bro_sis = Misc.sid_from_link(message.text)
    if not sid_bro_sis:
        if await is_it_command(message, state, excepts=('start',)):
            return
        await message.reply(
            Misc.MSG_INVALID_LINK + '\nПовторите, пожалуйста' ,
            reply_markup=Misc.reply_markup_cancel_row()
        )
        return
    data = await state.get_data()
    if uuid_whose := data.get('uuid'):
        response_whose = await Misc.check_owner_by_uuid(owner_tg_user=message.from_user, uuid=uuid_whose)
        response_bro_sis = await Misc.check_owner_by_sid(owner_tg_user=message.from_user, sid=sid_bro_sis)
        if response_whose and response_bro_sis:
            data_whose = response_whose['response_uuid']
            data_bro_sis = response_bro_sis['response_uuid']
            dl_whose = Misc.get_deeplink_with_name(data_whose)
            dl_bro_sis = Misc.get_deeplink_with_name(data_bro_sis)
            if data_whose['uuid'] == data_bro_sis['uuid']:
                await message.reply((
                    'Нельзя назначать брата или сестру между '
                    'одним и тем человеком.\n\n'
                    'Назначайте брата или сестру по новой'
                ))
            elif not data_whose.get('father') and not data_whose.get('mother'):
                await message.reply((
                    f'Назначить брата/сестру для {dl_whose} - это задать для {dl_bro_sis} родителей {dl_whose}. '
                    f'Но у {dl_whose} не заданы родители!\n\n'
                    f'Назначайте брата или сестру по новой'
                ))
            elif data_bro_sis.get('father') or data_bro_sis.get('mother'):
                await message.reply((
                    f'Назначить брата/сестру для {dl_whose} - это задать для {dl_bro_sis} родителей {dl_whose}. '
                    f'Но у {dl_bro_sis} уже задан папа и/или мама!\n\n'
                    f'Не исключено, что Вы ошиблись.\n'
                    f'Назначайте брата или сестру по новой или задавайте папу/маму для {dl_bro_sis}'
                ))
            else:
                is_father_set = is_mother_set = False
                if data_whose.get('father'):
                    post_op = dict(
                        tg_token=settings.TOKEN,
                        operation_type_id=OperationType.SET_FATHER,
                        user_id_from=data_bro_sis['uuid'],
                        user_id_to=data_whose['father']['uuid'],
                    )
                    logging.debug('post operation, payload: %s' % Misc.secret(post_op))
                    status, response = await Misc.api_request(
                        path='/api/addoperation',
                        method='post',
                        data=post_op,
                    )
                    logging.debug('post operation, status: %s' % status)
                    logging.debug('post operation, response: %s' % response)
                    if not (status == 200 or \
                       status == 400 and response.get('code') == 'already'):
                        if status == 400  and response.get('message'):
                            await message.reply((
                                f'Ошибка назначения папы для {dl_bro_sis}!\n'
                                f'{response["message"]}\n\n'
                                f'Назначайте брата/сестру по новой'
                            ))
                        else:
                            await message.reply(Misc.MSG_ERROR_API + '\nНазначайте брата/сестру по новой')
                    else:
                        is_father_set = True
                if (data_whose.get('father') and is_father_set or not data_whose.get('father')) and \
                   data_whose.get('mother'):
                    post_op = dict(
                        tg_token=settings.TOKEN,
                        operation_type_id=OperationType.SET_MOTHER,
                        user_id_from=data_bro_sis['uuid'],
                        user_id_to=data_whose['mother']['uuid'],
                    )
                    logging.debug('post operation, payload: %s' % Misc.secret(post_op))
                    status, response = await Misc.api_request(
                        path='/api/addoperation',
                        method='post',
                        data=post_op,
                    )
                    logging.debug('post operation, status: %s' % status)
                    logging.debug('post operation, response: %s' % response)
                    if not (status == 200 or \
                       status == 400 and response.get('code') == 'already'):
                        if status == 400  and response.get('message'):
                            await message.reply(
                                f'Ошибка назначения мамы для {dl_bro_sis}!\n' + \
                                f'{response["message"]}\n\n' + \
                                '' if is_father_set else 'Назначайте брата/сестру по новой' 
                            )
                        else:
                            await message.reply(
                                Misc.MSG_ERROR_API + \
                                '\nпри назначении мамы для ' + dl_bro_sis + \
                                '' if is_father_set else '\nНазначайте брата/сестру по новой'
                            )
                    else:
                        is_mother_set = True
                if is_father_set or data_whose.get('mother') and is_mother_set:
                    status, response = await Misc.get_user_by_uuid(uuid=data_bro_sis['uuid'])
                    if status == 200:
                        await message.reply(f'{dl_bro_sis} имеет тех же родителей, что и {dl_whose}')
                        await Misc.show_card(
                            profile=response,
                            profile_sender=response_whose,
                            tg_user_sender=message.from_user,
                        )
        else:
            await message.reply((
                'Можно назначать брата или сестру только между Вами '
                'или профилями, которыми Вы владеете.\n\n'
                'Назначайте брата или сестру по новой'
            ))
    await state.clear()


@router.callback_query(F.data.regexp(r'^(%s|%s)%s' % (
        KeyboardType.NEW_BRO, KeyboardType.NEW_SIS,
        KeyboardType.SEP,
    )), StateFilter(FSMbroSis.ask))
async def cbq_new_bro_sis_gender(callback: CallbackQuery, state: FSMContext):
    if not (uuid := Misc.get_uuid_from_callback(callback)):
        await state.clear(); await callback.answer()
        return
    data = await state.get_data()
    if not data.get('uuid') or data['uuid'] != uuid:
        await state.clear(); await callback.answer()
        return
    gender = 'm' \
        if callback.data.split(KeyboardType.SEP)[0] == str(KeyboardType.NEW_BRO) \
        else 'f'
    await state.update_data(gender=gender)
    brata_sestru = "брата" if gender == "m" else "сестру"
    response = await Misc.check_owner_by_uuid(owner_tg_user=callback.from_user, uuid=uuid)
    if not response:
        await callback.message.reply((
            f'Можно назначить {brata_sestru} только Вам '
            f'или профилю, которым Вы владеете.\n\n'
            f'Назначайте {brata_sestru} по новой'
        ))
        await state.clear(); await callback.answer()
        return
    data_whose = response['response_uuid']
    if not data_whose.get('father') and not data_whose.get('mother'):
        await callback.message.reply((
            f'Назначить {brata_sestru} для <b>{data_whose["first_name"]}</b> - '
            f'это внести профиль с теми же родителям. '
            f'Но у <b>{data_whose["first_name"]}</b> не заданы родители!\n\n'
            f'Назначайте {brata_sestru} по новой'
        ))
        await state.clear(); await callback.answer()
        return
    await state.set_state(FSMbroSis.new)
    await callback.message.reply((
            f'Укажите ФИО {"БРАТА" if gender == "m" else "СЕСТРЫ"} для:\n'
            f'{data_whose["first_name"]}\n'
            f'Например, {"Иван Иванович Иванов" if gender == "m" else "Мария Ивановна Иванова"}'
        ),
        reply_markup=Misc.reply_markup_cancel_row()
    )
    await callback.answer()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMbroSis.new))
async def put_new_bro_sis(message: Message, state: FSMContext):
    if await is_it_command(message, state):
        return
    data = await state.get_data()
    if data.get('uuid') and data.get('gender'):
        if message.content_type != ContentType.TEXT:
            await message.reply(
                Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + Misc.MSG_REPEATE_PLEASE,
                reply_markup=Misc.reply_markup_cancel_row()
            )
            return
        first_name = Misc.strip_text(message.text)
        brata_sestru = "брата" if data["gender"] == "m" else "сестру"
        response_whose = await Misc.check_owner_by_uuid(owner_tg_user=message.from_user, uuid=data['uuid'])
        if response_whose:
            data_whose = response_whose['response_uuid']
            dl_whose = Misc.get_deeplink_with_name(data_whose)
            if not data_whose.get('father') and not data_whose.get('mother'):
                await message.reply((
                    f'Назначить {brata_sestru} - это задать для <u>{first_name}</u> родителей {dl_whose}. '
                    f'Но у {dl_whose} не заданы родители!\n\n'
                    f'Назначайте {brata_sestru} по новой'
                ))
            else:
                is_father_set = is_mother_set = False
                data_bro_sis = None
                payload_post = dict(
                    tg_token=settings.TOKEN,
                    first_name=first_name,
                    gender=data['gender'],
                    owner_id=response_whose['user_id'],
                )
                if data_whose.get('father'):
                    payload_post.update(
                        link_id=data_whose['father']['uuid'],
                        link_relation='link_is_father',
                    )
                    logging.debug('post new brother or sister & set father payload: %s' % Misc.secret(payload_post))
                    status, data_bro_sis = await Misc.api_request(
                        path='/api/profile',
                        method='post',
                        data=payload_post,
                    )
                    logging.debug('post new brother or sister & set father, status: %s' % status)
                    logging.debug('post new brother or sister & set father, response: %s' % data_bro_sis)
                    if status == 200:
                        is_father_set = True
                        dl_bro_sis = Misc.get_deeplink_with_name(data_bro_sis)
                    else:
                        if status == 400  and data_bro_sis.get('message'):
                            await message.reply(
                                f'Ошибка!\n{data_bro_sis["message"]}\n\nНазначайте {brata_sestru} по новой'
                            )
                        else:
                            await message.reply(Misc.MSG_ERROR_API)
                if (data_whose.get('father') and is_father_set or not data_whose.get('father')) and \
                    data_whose.get('mother'):
                    if is_father_set:
                        # когда связывали с папой, уже появился профиль в системе: data_bro_sis
                        payload_op = dict(
                            tg_token=settings.TOKEN,
                            operation_type_id=OperationType.SET_MOTHER,
                            user_id_from=data_bro_sis['uuid'],
                            user_id_to=data_whose['mother']['uuid'],
                        )
                        logging.debug('post operation, payload: %s' % Misc.secret(payload_op))
                        status, response = await Misc.api_request(
                            path='/api/addoperation',
                            method='post',
                            data=payload_op,
                        )
                        logging.debug('post operation, status: %s' % status)
                        logging.debug('post operation, response: %s' % response)
                        if not (status == 200 or \
                           status == 400 and response.get('code') == 'already'):
                            repr_bro_sis = dl_bro_sis if is_father_set else first_name
                            if status == 400  and response.get('message'):
                                await message.reply(
                                    f'Ошибка назначения мамы для {repr_bro_sis}!\n' + \
                                    f'{response["message"]}\n\n' + \
                                    '' if is_father_set else f'Назначайте {brata_sestru} по новой'
                                )
                            else:
                                await message.reply(
                                    Misc.MSG_ERROR_API + \
                                    '\nпри назначении мамы для ' + repr_bro_sis + \
                                    '' if is_father_set else f'\nНазначайте {brata_sestru} по новой'
                                )
                        if status == 200:
                            is_mother_set = True
                    else:
                        payload_post.update(
                            link_id=data_whose['mother']['uuid'],
                            link_relation='link_is_mother',
                        )
                        logging.debug('post new brother or sister & set mother payload: %s' % Misc.secret(payload_post))
                        status, data_bro_sis = await Misc.api_request(
                            path='/api/profile',
                            method='post',
                            data=payload_post,
                        )
                        logging.debug('post new brother or sister & set mother, status: %s' % status)
                        logging.debug('post new brother or sister & set father, response: %s' % data_bro_sis)
                        if status == 200:
                            is_mother_set = True
                            dl_bro_sis = Misc.get_deeplink_with_name(data_bro_sis)
                        else:
                            if status == 400  and data_bro_sis.get('message'):
                                await message.reply(
                                    f'Ошибка!\n{data_bro_sis["message"]}\n\nНазначайте {brata_sestru} по новой'
                                )
                            else:
                                await message.reply(Misc.MSG_ERROR_API)
                if is_father_set or data_whose.get('mother') and is_mother_set:
                    status, response = await Misc.get_user_by_uuid(uuid=data_bro_sis['uuid'])
                    if status == 200:
                        await message.reply(f'{dl_bro_sis} имеет тех же родителей, что и {dl_whose}')
                        await Misc.show_card(
                            profile=response,
                            profile_sender=response_whose,
                            tg_user_sender=message.from_user,
                        )
        else:
            await message.reply((
                f'Можно назначить {brata_sestru} только Вам '
                f'или профилю, которым Вы владеете.\n\n'
                f'Назначайте {brata_sestru} по новой'
            ))
    await state.clear()
