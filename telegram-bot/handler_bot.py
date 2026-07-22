# handler_bot.py
#
# Команды и сообщения в бот
#
# Все команды в бот должны быть здесь. После команд в бот идет обработка
# любого сообщения

import re, redis
from urllib.parse import urlparse

from aiogram import Router, F, html
from aiogram.types import Message, CallbackQuery, ContentType,  \
                            MessageOriginUser, MessageOriginHiddenUser, MessageOriginChat, MessageOriginChannel, \
                            InlineKeyboardMarkup, InlineKeyboardButton, \
                            BufferedInputFile, LinkPreviewOptions
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter, CommandStart, CommandObject
from aiogram.fsm.state import StatesGroup, State

import logging
import settings

from common import FSMnewPerson, FSMgeo, FSMdelete
from common import Misc, KeyboardType, OperationType, Rcache, MeetId

import pymorphy3
MorphAnalyzer = pymorphy3.MorphAnalyzer()
import me
dp, bot, bot_data = me.dp, me.bot, me.bot_data

router = Router()

class FSMquery(StatesGroup):
    ask = State()

class FSMnewOrg(StatesGroup):
    ask = State()

class FSMagreeToRules(StatesGroup):
    ask = State()


def _command_tail(text):
    parts = (text or '').split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ''


def _vpn_profile_payload(profile, action='get', **kwargs):
    payload = dict(
        tg_token=settings.TOKEN,
        user_uuid=profile['uuid'],
        action=action,
    )
    payload.update(kwargs)
    return payload


async def _vpn_sender_profile(message):
    status_sender, profile = await Misc.post_tg_user(message.from_user)
    if status_sender != 200:
        await message.reply(Misc.MSG_ERROR_API)
        return None
    return profile


async def _reply_vpn_profile(message, response):
    profile = response.get('profile') or {}
    subscription_url = profile.get('subscription_url') or ''
    config_uri = profile.get('config_uri') or ''
    label = profile.get('label') or 'vpn'
    text = (
        '<b>VPN профиль</b>\n'
        f'Метка: <code>{html.quote(label)}</code>\n'
    )
    if subscription_url:
        text += f'Подписка: <code>{html.quote(subscription_url)}</code>\n'
    if config_uri:
        text += f'\nКонфигурация:\n<code>{html.quote(config_uri)}</code>\n'
    if profile.get('token_expires_at'):
        text += '\nТокен подписки обновляется еженедельно.'
    await message.reply(text)
    qr_value = subscription_url or config_uri
    if qr_value:
        qr_profile = dict(username=label, photo='')
        bytes_io = await Misc.get_qrcode(qr_profile, qr_value)
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=BufferedInputFile(bytes_io.getvalue(), filename=bytes_io.name),
        )


def _format_vpn_money(value, currency):
    if value in (None, ''):
        return 'не задано'
    return f'{value} {currency}'.strip()


def _vpn_dashboard_text(response):
    runway = response.get('runway') or {}
    funding = response.get('funding') or {}
    usage_graph = response.get('usage_graph') or {}
    currency = funding.get('currency') or runway.get('currency') or ''
    days_left = runway.get('days_left')
    days_text = str(days_left) if days_left is not None else 'не задано'
    text = (
        '<b>VPN: текущий сервер</b>\n'
        f'Оплачен до: {runway.get("prepaid_until") or "не задано"}\n'
        f'Запас: {days_text} дней\n'
        f'Следующий платеж: {_format_vpn_money(funding.get("upcoming_payment_amount"), currency)}\n'
        f'Активные пользователи: {funding.get("active_users", 0)}\n'
        f'Справедливая доля: {_format_vpn_money(funding.get("fair_share_per_active_user"), currency)}\n'
        f'Донаты: {_format_vpn_money(funding.get("donations_received"), currency)}\n'
    )
    highlights = funding.get('donor_highlights') or []
    if highlights:
        text += '\n<b>Спасибо за поддержку</b>\n'
        for item in highlights:
            text += f'{html.quote(item["name"])}: {item["amount"]} {item["currency"]}\n'
    for period_key, caption in (('week', 'Неделя'), ('month', 'Месяц')):
        text += f'\n<b>{caption}: группы расхода</b>\n'
        for item in usage_graph.get(period_key, []):
            text += f'{item["band"]}: {item["count"]}\n'
    exact_users = response.get('exact_users') or []
    if exact_users:
        text += '\n<b>Точный расход, админ</b>\n'
        for item in exact_users[:30]:
            text += (
                f'{html.quote(item["first_name"] or item["username"] or item["label"])}: '
                f'{item["week_gb"]} GB/week, {item["month_gb"]} GB/month\n'
            )
    return text


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^graph$', flags=re.I)),
)
async def cmd_graph(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_graph command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    inline_btn_all_users = InlineKeyboardButton(
        text='Отношения участников',
        login_url=Misc.make_login_url(
            redirect_path=settings.GRAPH_HOST + '/?rod=on&dover=on&withalone=on',
            keep_user_data='on'
    ))
    inline_btn_recent = InlineKeyboardButton(
        text='Недавно добавленные',
        login_url=Misc.make_login_url(
            redirect_path=settings.GRAPH_HOST + '/?f=0&q=50',
            keep_user_data='on'
    ))
    await message.reply(
        text='Выберите тип графика',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[inline_btn_all_users],[inline_btn_recent]])

    )


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^ya$', flags=re.I)),
)
async def cmd_ya(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_ya command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender != 200:
        await message.reply(Misc.MSG_ERROR_API)
        return
    await Misc.show_card(
        profile=response_sender,
        profile_sender=response_sender,
        tg_user_sender=message.from_user,
    )


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^help$', flags=re.I)),
)
async def cmd_help(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_help command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    await show_start(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^setplace$', flags=re.I)),
)
async def cmd_setplace(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_setplace command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    await Misc.prompt_location(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^(?:new|new_person)$', flags=re.I)),
)
async def cmd_new_person(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_new_person command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender == 200:
        if not Misc.is_power(response_sender):
            logging.debug(f"User lacks permissions for new_person command - User: {message.from_user.username} (ID: {message.from_user.id})")
            return
        await state.set_state(FSMnewPerson.ask)
        await state.update_data(uuid=response_sender['uuid'])
        await message.reply(Misc.PROMPT_NEW_IOF, reply_markup=Misc.reply_markup_cancel_row())


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^new_org$', flags=re.I)),
)
async def cmd_new_org(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_new_org command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender == 200:
        if not Misc.is_power(response_sender):
            logging.debug(f"User lacks permissions for new_org command - User: {message.from_user.username} (ID: {message.from_user.id})")
            return
        await state.set_state(FSMnewOrg.ask)
        await message.reply(Misc.PROMPT_NEW_ORG, reply_markup=Misc.reply_markup_cancel_row())


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^(?:findpotr|findvozm|findperson)$', flags=re.I)),
)
async def cmd_find(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_find command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    message_text = message.text.split()[0].lstrip('/')
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender == 200:
        if not Misc.is_power(response_sender):
            logging.debug(f"User lacks permissions for find command - User: {message.from_user.username} (ID: {message.from_user.id})")
            return
        if message_text == 'findpotr':
            what = 'query_wish'
        elif message_text == 'findvozm':
            what = 'query_ability'
        elif message_text == 'findperson':
            what = 'query_person'
        else:
            return
        await state.set_state(FSMquery.ask)
        await state.update_data(what=what)
        await message.reply(Misc.PROMPT_QUERY[what], reply_markup=Misc.reply_markup_cancel_row())


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^meet$', flags=re.I)),
)
async def cmd_meet(message: Message, state: FSMContext, profile=None):
    logging.debug(f"Executing cmd_meet command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    if profile:
        status = 200
    else:
        status, profile = await Misc.post_tg_user(message.from_user)
    if status == 200:
        data = dict(profile_from = profile, profile_to=None)
        await process_meet_from_deeplink_and_command(message, state, data)
    else:
        await message.reply(Misc.MSG_ERROR_API)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^(?:trust|thank)$', flags=re.I)),
)
async def cmd_trust_thank(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_trust_thank command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    command = message.text.strip('/').strip().lower()
    status, profile = await Misc.post_tg_user(message.from_user)
    if status == 200:
        command_to_data = dict(
            trust=dict(prefix='t',  caption='Доверяю %(link)s'),
            thank=dict(prefix='th', caption='Благодарить %(link)s'),
        )
        url = (
            f'https://t.me/{bot_data.username}'
            f'?start={command_to_data[command]["prefix"]}-{profile["username"]}'
        )
        link = f'<a href="{url}">{profile["first_name"]}</a>'
        caption = command_to_data[command]["caption"] % dict(link=link)
        bytes_io = await Misc.get_qrcode(profile, url)
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=BufferedInputFile(bytes_io.getvalue(), filename=bytes_io.name),
            caption=caption,
        )

@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^stat$', flags=re.I)),
)
async def cmd_stat(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_stat command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status, response = await Misc.api_request(
        path='/api/bot/stat',
        method='get',
    )
    if status == 200 and response:
        reply = (
            '<b>Статистика</b>\n'
            '\n'
            f'Пользователи: {response["active"]}\n'
            f'Стартовали бот: {response["did_bot_start"]}\n'
            f'Указали местоположение: {response["with_geodata"]}\n'
            f'Cозданные профили: {response["owned"]}\n'
            f'Всего профилей: {response["active"] + response["owned"]}\n'
            f'Родственных связей: {response["relations"]}\n'
            f'Доверий: {response["trusts"]}\n'
            f'Недоверий: {response["mistrusts"]}\n'
            f'Знакомств: {response["acqs"]}\n'
        )
        await message.answer(reply)

@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^map$', flags=re.I)),
)
async def cmd_map(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_map command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    await bot.send_message(
        message.from_user.id,
        text=Misc.get_html_a(href=settings.MAP_HOST, text='Карта участников'),
    )


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^feedback$', flags=re.I)),
)
async def cmd_feedback(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_feedback command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    await message.reply(
        Misc.get_html_a(settings.BOT_CHAT['href'], settings.BOT_CHAT['caption']),
    )


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^vpn$', flags=re.I)),
)
async def cmd_vpn(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_vpn command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    profile = await _vpn_sender_profile(message)
    if not profile:
        return
    status_vpn, response_vpn = await Misc.api_request(
        path='/api/vpn/profile/',
        method='post',
        json=_vpn_profile_payload(profile),
    )
    if status_vpn == 200 and response_vpn:
        await _reply_vpn_profile(message, response_vpn)
    else:
        await message.reply((response_vpn or {}).get('message') or Misc.MSG_ERROR_API)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^fresh$', flags=re.I)),
)
async def cmd_fresh(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_fresh command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    profile = await _vpn_sender_profile(message)
    if not profile:
        return
    feedback_text = _command_tail(message.text)
    payload = _vpn_profile_payload(profile, action='fresh')
    if feedback_text:
        payload['feedback_text'] = feedback_text
    status_vpn, response_vpn = await Misc.api_request(
        path='/api/vpn/profile/',
        method='post',
        json=payload,
    )
    if status_vpn == 200 and response_vpn:
        await _reply_vpn_profile(message, response_vpn)
        if response_vpn.get('donation_prompt'):
            await message.reply(response_vpn['donation_prompt'])
        if response_vpn.get('ticket'):
            await message.reply(
                'Заявка записана. Метка: '
                f'<code>{html.quote(response_vpn["ticket"]["artifact_label"])}</code>'
            )
    else:
        artifact_label = (response_vpn or {}).get('artifact_label')
        text = (response_vpn or {}).get('message') or Misc.MSG_ERROR_API
        if artifact_label:
            text += f'\nМетка: <code>{html.quote(artifact_label)}</code>'
        await message.reply(text)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^my_usage$', flags=re.I)),
)
async def cmd_my_usage(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_my_usage command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    profile = await _vpn_sender_profile(message)
    if not profile:
        return
    status_usage, response_usage = await Misc.api_request(
        path='/api/vpn/my_usage/',
        method='get',
        params=dict(tg_token=settings.TOKEN, user_uuid=profile['uuid']),
    )
    if status_usage == 200 and response_usage:
        await message.reply(
            '<b>Ваш VPN расход</b>\n'
            f'Неделя: {response_usage["week"]["total_gb"]} GB\n'
            f'Месяц: {response_usage["month"]["total_gb"]} GB'
        )
    else:
        await message.reply((response_usage or {}).get('message') or Misc.MSG_ERROR_API)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^vpn_dashboard$', flags=re.I)),
)
async def cmd_vpn_dashboard(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_vpn_dashboard command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    profile = await _vpn_sender_profile(message)
    if not profile:
        return
    params = dict(tg_token=settings.TOKEN, user_uuid=profile['uuid'])
    if profile.get('is_power'):
        params['exact'] = 1
    status_dashboard, response_dashboard = await Misc.api_request(
        path='/api/vpn/dashboard/',
        method='get',
        params=params,
    )
    if status_dashboard == 200 and response_dashboard:
        await message.reply(_vpn_dashboard_text(response_dashboard))
    else:
        await message.reply((response_dashboard or {}).get('message') or Misc.MSG_ERROR_API)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^connect_friend$', flags=re.I)),
)
async def cmd_connect_friend(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_connect_friend command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    profile = await _vpn_sender_profile(message)
    if not profile:
        return
    status_friend, response_friend = await Misc.api_request(
        path='/api/vpn/connect_friend/',
        method='post',
        json=dict(tg_token=settings.TOKEN, user_uuid=profile['uuid']),
    )
    if status_friend == 200 and response_friend:
        await message.reply(
            'Ссылка для друга:\n'
            f'{html.quote(response_friend["url"])}\n\n'
            'MTProto можно использовать только как временный вход в Telegram. '
            'VPN профиль Doverabot выдаст другу лично.'
        )
    else:
        await message.reply((response_friend or {}).get('message') or Misc.MSG_ERROR_API)


async def show_start(message, state, set_state=True):
    status, response = await Misc.get_template('start')
    if status == 200 and response:
        inline_btn_agree = InlineKeyboardButton(
            text='Соглашаюсь',
            callback_data=Misc.CALLBACK_DATA_KEY_TEMPLATE % dict(
            keyboard_type=KeyboardType.AGREE_TO_RULES,
            sep=KeyboardType.SEP,
        ))
        if set_state:
            await state.set_state(FSMagreeToRules.ask)
        await message.reply(
            response,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[ [inline_btn_agree] ])
        )

@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^start$', flags=re.I)),
)
async def cmd_start(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_start command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    arg = Misc.arg_deeplink(message.text)
    if not arg:
        # команда /start
        if m := re.search(r'^\s*\/start\s+(.+)', message.text, flags=re.I):
            arg = m.group(1) or ''
    if not arg:
        # Просто /start
        await show_start(message, state)
        return

    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender != 200:
        await message.reply(Misc.MSG_ERROR_API)
        return
    if m := re.search(r'^(t|th)\-([0-9a-z]{10})$', arg, flags=re.I):
        status_to, profile_to = await Misc.get_user_by_sid(m.group(2))
        if status_to == 200:
            await Misc.put_attitude(data = dict(
                tg_user_sender=message.from_user,
                profile_from = response_sender,
                profile_to = profile_to,
                operation_type_id = OperationType.start_prefix_to_op(m.group(1)),
                callback=None,
                message_to_forward_id = None,
                group_member=None,
                is_thank_card=False,
                state=state,
            ))

    elif m := re.search((
                r'^offer\-([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})'
                r'(?:-userId-([a-z0-9]{10})){0,1}$'
            ),
            arg, flags=re.I
        ):
            from handler_offer import Offer
            status_offer, response_offer = await Offer.post_offer_answer(m.group(1), response_sender, [-1])
            if status_offer == 200:
                offer = response_offer['offer']
                profile_ref = None
                if m.group(2):
                    status_ref, profile_ref = await Misc.get_user_by_sid(m.group(2))
                    if status_ref != 200 or profile_ref['owner']:
                        profile_ref = None
                if not profile_ref:
                    profile_ref = offer['owner']
                await Offer.show_offer(
                    response_sender, offer, message,
                    username_href=response_sender['username'],
                    profile_ref=profile_ref,
                )
                payload_ref = dict(
                    tg_token=settings.TOKEN,
                    offer_uuid=offer['uuid'],
                    username_from=response_sender['username'],
                    username_to=profile_ref['username'],
                )
                logging.debug('post_offer_referrer, payload: %s' % Misc.secret(payload_ref))
                status_ref, response_ref = await Misc.api_request(
                    path='/api/offer/ref',
                    method='post',
                    json=payload_ref,
                )
                logging.debug('post_offer_referrer, status: %s' % status_ref)
                logging.debug('post_offer_referrer, response: %s' % response_ref)
            else:
                await message.reply('Опрос-предложение не найдено')

    elif m := re.search(
            r'^rent\-([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})$',
            arg, flags=re.I
        ):
        from handler_rental import Rental
        status_rental, response_rental = await Rental.get_offer(m.group(1), response_sender['uuid'])
        if status_rental == 200:
            await Rental.show_offer(message, response_sender, response_rental['offer'])
        else:
            await message.reply('Объявление проката не найдено')

    elif m := re.search(
            r'^([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})$',
            arg, flags=re.I
        ):
        status_to, profile_to = await Misc.get_user_by_uuid(m.group(1))
        if status_to == 200:
            await Misc.show_card(
                profile=profile_to,
                profile_sender=response_sender,
                tg_user_sender=message.from_user,
            )
        else:
            await message.reply('Пользователь не найден')

    elif m := re.search(r'^([0-9a-z]{10})$', arg, flags=re.I):
        status_to, profile_to = await Misc.get_user_by_sid(m.group(1))
        if status_to == 200:
            await Misc.show_card(
                profile=profile_to,
                profile_sender=response_sender,
                tg_user_sender=message.from_user,
            )
        else:
            await message.reply('Пользователь не найден')

    elif m := re.search(
            r'^auth_redirect\-([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})$',
            arg, flags=re.I
        ):
            status_token, response_token = await Misc.api_request(
                path='/api/token/url/',
                method='GET',
                params=dict(token=m.group(1)))
            if status_token == 200:
                redirect_path = response_token['url']
                inline_btn_redirect = InlineKeyboardButton(
                    text='Продолжить',
                    login_url=Misc.make_login_url(
                        redirect_path=redirect_path,
                        keep_user_data='on'
                    ),
                )
                buttons = [ [inline_btn_redirect] ]
                if redirect_path.lower().startswith(settings.VOTE_URL):
                    if m := re.search(r'\#(\S+)$', redirect_path):
                        if m := Misc.get_youtube_id(m.group(1)):
                            youtube_id, youtube_link = m
                            await answer_youtube_message(message, youtube_id, youtube_link)
                            return
                auth_url_parse = urlparse(redirect_path)
                auth_text = ''
                if auth_url_parse.hostname:
                    for auth_domain in settings.AUTH_PROMPT_FOR_DOMAIN:
                        if re.search(re.escape(auth_domain) + '$', auth_url_parse.hostname):
                            auth_text = settings.AUTH_PROMPT_FOR_DOMAIN[auth_domain]
                            break
                redirect_path_new = redirect_path
                if not auth_text:
                    # Чтобы телеграм не предлагал ссылку, берется после последнего http(s)://,
                    # впереди ставится троеточие
                    #
                    if m:=re.search(r'(?:https?\:\/\/)?([^\:\#]+)$', redirect_path):
                        redirect_path_new = '...' + m.group(1)
                    auth_text = f'Нажмите <u>Продолжить</u> для доступа к:\n{redirect_path_new}'
                await message.reply(
                    auth_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                )
            else:
                await message.reply('Ссылка устарела или не найдена. Получите новую.')

    elif m := re.search(r'^m\-([0-9a-z]{11})$', arg, flags=re.I):
        if not response_sender['is_active']:
            await message.reply(Misc.MSG_NOT_SENDER_NOT_ACTIVE)
            return
        profile_to = await MeetId.profile_by_meetId(m.group(1))
        if profile_to:
            data = dict(profile_from = response_sender, profile_to=profile_to)
            await process_meet_from_deeplink_and_command(message, state, data)

    elif arg == 'setplace':
        await Misc.prompt_location(message, state)

    elif arg == 'meet':
        await cmd_meet(message, state, profile=response_sender)

    elif arg == 'vpn':
        await cmd_vpn(message, state)

    else:
        await message.reply(f'Такая команда — /start {arg} — не предусмотрена!')


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^getowned$', flags=re.I)),
)
async def cmd_getowned(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_getowned command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status, response_from = await Misc.post_tg_user(message.from_user)
    if status == 200:
        if not Misc.is_power(response_from):
            logging.debug(f"User lacks permissions for getowned command - User: {message.from_user.username} (ID: {message.from_user.id})")
            return
        try:
            status, a_response_to = await Misc.api_request(
                path='/api/profile',
                method='get',
                params=dict(uuid_owner=response_from['uuid']),
            )
            logging.debug('get_tg_user_sender_owned data in api, status: %s' % status)
            logging.debug('get_tg_user_sender_owned data in api, response: %s' % a_response_to)
        except:
            return

        if a_response_to:
            bot_data = await bot.get_me()
            await Misc.show_deeplinks(a_response_to, message)
        else:
            await message.reply('У вас нет запрошенных данных')

@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^offer|offer_multi$', flags=re.I)),
)
async def cmd_offer(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_offer command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_offer import Offer
    await Offer.cmd_offer(message, state)

@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^rent$', flags=re.I)),
)
async def cmd_rent(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_rent command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_rental import Rental
    await Rental.cmd_rent(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^rent_offer$', flags=re.I)),
)
async def cmd_rent_offer(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_rent_offer command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_rental import Rental
    await Rental.cmd_rent_offer(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^rent_search$', flags=re.I)),
)
async def cmd_rent_search(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_rent_search command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_rental import Rental
    await Rental.cmd_rent_search(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^rent_my$', flags=re.I)),
)
async def cmd_rent_my(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_rent_my command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_rental import Rental
    await Rental.cmd_rent_my(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^rent_history$', flags=re.I)),
)
async def cmd_rent_history(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_rent_history command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    from handler_rental import Rental
    await Rental.cmd_rent_history(message, state)


@router.message(
    F.text,
    F.chat.type.in_((ChatType.PRIVATE,)),
    StateFilter(None),
    Command(re.compile('^quit$', flags=re.I)),
)
async def cmd_quit(message: Message, state: FSMContext):
    logging.debug(f"Executing cmd_quit command - User: {message.from_user.username} (ID: {message.from_user.id}), Message: {message.text}")
    status, profile = await Misc.post_tg_user(message.from_user)
    if status == 200:
        if profile['is_active']:
            await state.set_state(FSMdelete.ask)
            await state.update_data(uuid=profile['uuid'], owner_id=profile['user_id'])
            prompt, reply_markup = Misc.message_delete_user(profile, owner=profile)
            await message.reply(prompt, reply_markup=reply_markup)
        else:
            await message.reply('Вы уже обезличены')


# Команды в бот закончились.
# Просто сообщение в бот. Должно здесь идти после всех команд в бот

@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(None))
async def message_to_bot(message: Message, state: FSMContext):

    # Deeplink. Если щелкнуть по нему, все ок. Если загнать в бот, то никакой реакции
    #
    if message.content_type == ContentType.TEXT and  Misc.arg_deeplink(message.text):
        await cmd_start(message, state)
        return

    show_response = True
    if message.media_group_id:
        if r := redis.Redis(**settings.REDIS_CONNECT):
            check_str = (
                f'{Rcache.MEDIA_GROUP_PREFIX}'
                f'{message.media_group_id}'
            )
            if r.get(check_str):
                show_response = False
            else:
                r.set(
                    name=check_str,
                    value='1',
                    ex=Rcache.MEDIA_GROUP_TTL,
                )
            r.close()
    if not show_response:
        return

    tg_user_sender = message.from_user
    reply = ''
    is_forward = is_forward_from_other = found_username = False
    tg_chat_forwarded = None
    if tg_user_sender.is_bot:
        reply = 'Сообщения от ботов пока не обрабатываются'
    elif message.content_type == ContentType.PINNED_MESSAGE:
        return
    if message.forward_origin:
        if type(message.forward_origin) == MessageOriginUser:
            tg_user_forwarded = message.forward_origin.sender_user
            is_forward = True
            is_forward_from_other = tg_user_forwarded.id != tg_user_sender.id
        elif type(message.forward_origin) == MessageOriginHiddenUser:
            reply = (
                'Автор исходного сообщения '
                '<a href="https://telegram.org/blog/unsend-privacy-emoji#anonymous-forwarding">запретил</a> '
                'идентифицировать себя в пересылаемых сообщениях'
            )
        elif type(message.forward_origin) == MessageOriginChat:
            is_forward = is_forward_from_other = True
            tg_chat_forwarded = message.forward_origin.sender_chat
        elif type(message.forward_origin) == MessageOriginChannel:
            is_forward = is_forward_from_other = True
            tg_chat_forwarded = message.forward_origin.chat
    else:
        if message.content_type != ContentType.TEXT:
            reply = 'Сюда можно слать текст для поиска, включая @username, или пересылать сообщения любого типа'

    if reply:
        await message.reply(reply)
        return

    status_from, response_from = await Misc.post_tg_user(tg_user_sender)
    if status_from != 200:
        await message.reply(Misc.MSG_ERROR_API)
        return

    message_text = getattr(message, 'text', '') and message.text.strip() or ''
    if is_forward_from_other:
        if tg_chat_forwarded:
            status_to, response_to = await Misc.post_tg_chat(tg_chat_forwarded)
        else:
            status_to, response_to = await Misc.post_tg_user(tg_user_forwarded, did_bot_start=False)
        if status_to != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await Misc.show_card(
            profile=response_to,
            profile_sender=response_from,
            tg_user_sender=tg_user_sender,
            message_to_forward_id = message.message_id,
        )
        usernames, text_stripped = Misc.get_text_usernames(message_text)
        if usernames:
            logging.debug('@usernames found in message text\n')
            payload_username = dict(tg_username=','.join(usernames),)
            status, response = await Misc.api_request(
                path='/api/profile',
                method='get',
                params=payload_username,
            )
            logging.debug('get by username, status: %s' % status)
            logging.debug('get by username, response: %s' % response)
            if status == 200 and response:
                await Misc.show_deeplinks(response, message,)
        return

    # not forwarded or forwarded from me

    a_found = []
    if re.fullmatch(r'@[A-Za-z0-9_]{5,32}', message_text):
        status, profile = await Misc.get_or_create_tg_username(message_text[1:])
        if status != 200:
            await message.reply(Misc.MSG_ERROR_API)
            return
        await Misc.show_card(
            profile=profile,
            profile_sender=response_from,
            tg_user_sender=tg_user_sender,
        )
        return
    if message_text.startswith('/'):
        await message.reply('Не известная команда')
        return
    if len(message_text) < settings.MIN_LEN_SEARCHED_TEXT:
        await message.reply(
            f'Поиск участников по:\n'
            '\n'
            '- @имени участника в телеграме,\n'
            '- фамилии, имени, возможностям, потребностям.\n'
            '\n'
            f'Минимальное число символов в тексте для поиска: {settings.MIN_LEN_SEARCHED_TEXT}\n'
            '\n'
            'Также можно переслать сюда сообщение от любого пользователя телеграма\n'
            '\n'
            'Дальнейшие действия будут Вам предложены\n'
        )
        return
    if m := Misc.get_youtube_id(message_text):
        youtube_id, youtube_link = m
        await answer_youtube_message(message, youtube_id, youtube_link)
        return

    search_phrase = ''
    usernames, text_stripped = Misc.get_text_usernames(message_text)
    if text_stripped:
        search_phrase = Misc.text_search_phrase(
            text_stripped,
            MorphAnalyzer,
        )
        if not search_phrase and not usernames:
            await message.reply(Misc.PROMPT_SEARCH_PHRASE_TOO_SHORT)
            return

    if usernames:
        logging.debug('@usernames found in message text\n')
        payload_username = dict(tg_username=','.join(usernames),)
        status, response = await Misc.api_request(
            path='/api/profile',
            method='get',
            params=payload_username,
        )
        logging.debug('get by username, status: %s' % status)
        logging.debug('get by username, response: %s' % response)
        if status == 200 and response:
            a_found += response
            found_username = True

    if search_phrase:
        status, response = await Misc.search_users('query', search_phrase)
        if status == 400 and response.get('code') and response['code'] == 'programming_error':
            if not found_username:
                await message.reply('Ошибка доступа к данным. Получили отказ по такой строке в поиске')
                return
        elif status == 200:
            if response:
                a_found += response
            elif not found_username:
                await message.reply(Misc.PROMPT_NOTHING_FOUND)
                return
        else:
            await message.reply(Misc.MSG_ERROR_API)
            return
    if a_found:
        await Misc.show_deeplinks(a_found, message)


commands_dict = {
    'graph': cmd_graph,
    'ya': cmd_ya,
    'help': cmd_help,
    'new': cmd_new_person,
    'new_person': cmd_new_person,
    'new_org': cmd_new_org,
    'findperson': cmd_find,
    'setplace': cmd_setplace,
    'meet': cmd_meet,
    'start': cmd_start,
    'stat': cmd_stat,
    'map': cmd_map,
    'feedback': cmd_feedback,
    'getowned': cmd_getowned,
    'offer': cmd_offer,
    'offer_multi': cmd_offer,
    'rent': cmd_rent,
    'rent_offer': cmd_rent_offer,
    'rent_search': cmd_rent_search,
    'rent_my': cmd_rent_my,
    'rent_history': cmd_rent_history,
    'quit': cmd_quit,
}


async def is_it_command(message: Message, state: FSMContext, excepts=[]):
    """
    Проверка, не обнаружилась ли команда, когда от пользователя ждут данных

    Если обнаружилась, то состояние обнуляется,
    сообщение пользователю, вызов функции, выполняющей команду
    """
    result = False
    if message.content_type == ContentType.TEXT:
        message_text = Misc.strip_text(message.text).lower()
        m = re.search(r'^\/(\S+)', message_text)
        if m:
            command = m.group(1)
            if command in commands_dict and command not in excepts:
                if state:
                    await state.clear()
                await message.reply('%s\n%s /%s' % (
                     Misc.MSG_YOU_CANCELLED_INPUT,
                     'Выполняю команду',
                     command
                ))
                result = True
                await commands_dict[command](message, state)
    return result


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMgeo.geo))
async def process_location_input(message: Message, state: FSMContext):
    """
    Записать местоположение пользователя телеграма или uuid в состоянии
    """
    logging.debug(f"Processing location input - User: {message.from_user.username} (ID: {message.from_user.id}), Content type: {message.content_type}")
    if message.content_type == ContentType.TEXT:
        if await is_it_command(message, state):
            return
    else:
        logging.debug(f"Invalid content type for location input - User: {message.from_user.username} (ID: {message.from_user.id})")
        await message.answer(Misc.MSG_ERR_GEO, reply_markup=Misc.reply_markup_cancel_row())
        return
    await put_location(message, state, show_card=True)
    await state.clear()


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMquery.ask))
async def process_find_input(message: Message, state: FSMContext):
    logging.debug(f"Processing find input - User: {message.from_user.username} (ID: {message.from_user.id}), Content type: {message.content_type}")
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    data = await state.get_data()
    try:
        what = data['what']
        logging.debug(f"Find query type: {what} - User: {message.from_user.username} (ID: {message.from_user.id})")
    except KeyError:
        logging.debug(f"No query type found in state - User: {message.from_user.username} (ID: {message.from_user.id})")
        pass
    else:
        a_found = None
        if message.content_type != ContentType.TEXT:
            logging.debug(f"Invalid content type for find query - User: {message.from_user.username} (ID: {message.from_user.id})")
            reply_markup = Misc.reply_markup_cancel_row()
            await message.reply(
                Misc.MSG_ERROR_TEXT_ONLY + '\n\n' +  Misc.PROMPT_QUERY[what],
                reply_markup=Misc.reply_markup_cancel_row(),
            )
            return
        if len(message.text.strip()) < settings.MIN_LEN_SEARCHED_TEXT:
            logging.debug(f"Search text too short - User: {message.from_user.username} (ID: {message.from_user.id})")
            reply = Misc.PROMPT_SEARCH_TEXT_TOO_SHORT
        else:
            search_phrase = Misc.text_search_phrase(
                message.text,
                MorphAnalyzer,
            )
            if not search_phrase:
                logging.debug(f"Search phrase could not be generated - User: {message.from_user.username} (ID: {message.from_user.id})")
                reply = Misc.PROMPT_SEARCH_PHRASE_TOO_SHORT
            else:
                logging.debug(f"Searching for: {search_phrase} - User: {message.from_user.username} (ID: {message.from_user.id})")
                status, a_found = await Misc.search_users(what, search_phrase)
                if status != 200:
                    logging.debug(f"Search API error - Status: {status} - User: {message.from_user.username} (ID: {message.from_user.id})")
                    a_found = None
                elif not a_found:
                    logging.debug(f"No results found - User: {message.from_user.username} (ID: {message.from_user.id})")
                    reply = Misc.PROMPT_NOTHING_FOUND
        if a_found:
            logging.debug(f"Found {len(a_found)} results - User: {message.from_user.username} (ID: {message.from_user.id})")
            await Misc.show_deeplinks(a_found, message)
        elif reply:
            await message.reply(reply)
    await state.clear()


async def put_location(message, state, show_card=False):
    """
    Записать местоположение пользователя телеграма

    В случае успеха:
        Если show_card == True, то вернуть профиль карточки с новыми координатами
        Вернуть профиль пользователя
    Иначе вернуть пустой словарь
    """
    result = {}
    reply_markup = None
    user_uuid = None
    data = await state.get_data()
    user_uuid = data.get('uuid')
    latitude = longitude = None
    tg_user_sender = message.from_user
    status_sender, response_sender = await Misc.post_tg_user(tg_user_sender)
    if status_sender == 200:
        if not user_uuid:
            user_uuid = response_sender.get('uuid')
        latitude, longitude = Misc.check_location_str(message.text)
        if latitude is None or longitude is None:
            logging.debug(f"Invalid location format - User: {message.from_user.username} (ID: {message.from_user.id}), Input: {message.text}")
            await message.answer(Misc.MSG_ERR_GEO, reply_markup=Misc.reply_markup_cancel_row())
            return
        else:
            status, response = await Misc.put_user_properties(
                uuid=user_uuid,
                latitude = latitude,
                longitude = longitude,
            )
            if status == 200:
                result = response
                if show_card:
                    await Misc.show_card(
                        profile=response,
                        profile_sender=response_sender,
                        tg_user_sender=tg_user_sender,
                    )
                    await message.reply('Координаты записаны', reply_markup=reply_markup)
            else:
                logging.debug(f"Failed to save location - User: {message.from_user.username} (ID: {message.from_user.id}), Status: {status}")
                await message.reply('Ошибка записи координат', reply_markup=reply_markup)
    return result


async def process_meet_from_deeplink_and_command(message, state, data):
    profile_from, profile_to = data['profile_from'], data['profile_to']
    if profile_to and profile_to['uuid'] == profile_from['uuid']:
        profile_to = None
    if not profile_to and not profile_from['did_meet']:
        # Зашел по команде /meet или по meet deeplink на самого себя
        if profile_from.get('is_power'):
            pass
        else:
            count_meet_invited = await Misc.count_meet_invited(profile_from['uuid'])
            if count_meet_invited and count_meet_invited.get('was_invited'):
                pass
            else:
                await bot.send_message(
                    message.from_user.id,
                    text='Присоединиться к игре можно только по ссылке-приглашению участника',
                )
                return

    if profile_from['did_meet']:
        await Misc.show_edit_meet(message.from_user.id, profile_from)
    else:
        text = \
'''Добро пожаловать в игру знакомств! Цель игры - соединить одиноких людей!

Чтобы играть:
- нажмите "Участвовать",
- заполните анкету,
- приглашайте одиноких,
- отмечайте симпатии,
- выбирайте предложения и
- встречайтесь!

Победители - покинувшие игру соединившиеся пары!

Нажимая "Участвовать", Вы соглашаетесь с публикацией Ваших анкетных данных и принятием ответственности за их достоверность!
Удачи!'''

        callback_data_template = Misc.CALLBACK_DATA_SID_TEMPLATE + '%(sid2)s%(sep)s'
        inline_btn_do = InlineKeyboardButton(
            text='Участвовать',
            callback_data=callback_data_template % dict(
            keyboard_type=KeyboardType.MEET_DO,
            sid=profile_from['username'],
            sid2=profile_to['username'] if profile_to else '',
            sep=KeyboardType.SEP,
        ))
        logging.info(f'MEET_LOG: {profile_from["first_name"]} ({profile_from["username"]}) got meet game invitation')
        buttons = [ [inline_btn_do] ]
        await bot.send_message(
            message.from_user.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMnewOrg.ask))
async def process_new_org_ask(message: Message, state: FSMContext):
    logging.debug(f"Processing new org input - User: {message.from_user.username} (ID: {message.from_user.id}), Content type: {message.content_type}")
    if message.content_type != ContentType.TEXT:
        logging.debug(f"Invalid content type for org creation - User: {message.from_user.username} (ID: {message.from_user.id})")
        await message.reply(
            Misc.MSG_ERROR_TEXT_ONLY + '\n\n' + \
            Misc.PROMPT_NEW_ORG,
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    if await is_it_command(message, state):
        return
    first_name = Misc.strip_text(message.text)
    if not first_name or len(first_name) < 5:
        logging.debug(f"Organization name too short or invalid - User: {message.from_user.username} (ID: {message.from_user.id}), Name: {first_name}")
        await message.reply(
            Misc.PROMPT_ORG_INCORRECT,
            reply_markup=Misc.reply_markup_cancel_row(),
        )
        return
    logging.debug(f"Creating organization: {first_name} - User: {message.from_user.username} (ID: {message.from_user.id})")
    status_sender, response_sender = await Misc.post_tg_user(message.from_user)
    if status_sender == 200:
        payload_org = dict(
            tg_token=settings.TOKEN,
            owner_id=response_sender['user_id'],
            first_name=first_name,
            is_org='1',
        )
        logging.debug('post new org, payload: %s' % Misc.secret(payload_org))
        status, response = await Misc.api_request(
            path='/api/profile',
            method='post',
            data=payload_org,
        )
        logging.debug('post new org, status: %s' % status)
        logging.debug('post new org, response: %s' % response)
        if status == 200:
            logging.debug(f"Organization created successfully - User: {message.from_user.username} (ID: {message.from_user.id}), Org: {first_name}")
            await message.reply('Добавлена организация')
            await Misc.show_card(
                profile=response,
                profile_sender=response_sender,
                tg_user_sender=message.from_user,
            )
    await state.clear()

async def answer_youtube_message(message, youtube_id, youtube_link):
    """
    На запрос авторизации на сайт голосования или в ответ на youtube ссылку в бот
    """
    reply = 'Коллективный разум:\n' + youtube_link
    redirect_path = settings.VOTE_URL + '#' + youtube_link
    inline_btn_redirect = InlineKeyboardButton(
        text='Продолжить',
        login_url=Misc.make_login_url(
            redirect_path=redirect_path,
            keep_user_data='on'
    ))
    inline_btn_scheme = InlineKeyboardButton(
        text='Схема',
        login_url=Misc.make_login_url(
            redirect_path=f'{settings.GRAPH_HOST}/?videoid={youtube_id}&source=yt',
            keep_user_data='on',
        ))
    inline_btn_map = InlineKeyboardButton(
        text='Карта',
        login_url=Misc.make_login_url(
            redirect_path=f'{settings.MAP_HOST}/?videoid={youtube_id}&source=yt',
            keep_user_data='on',
        ))
    buttons = [ [inline_btn_redirect], [inline_btn_scheme, inline_btn_map] ]
    await message.reply(
        reply,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        link_preview_options=LinkPreviewOptions(is_disabled=False),
    )


@router.message(F.chat.type.in_((ChatType.PRIVATE,)), StateFilter(FSMagreeToRules.ask))
async def process_agree_to_rules(message: Message, state: FSMContext):
    # Что бы не ввел, повтор правил
    await show_start(message, state, set_state=False)

@router.callback_query(F.data.regexp(Misc.RE_KEY_SEP % (
        KeyboardType.AGREE_TO_RULES,
        KeyboardType.SEP,
    )), StateFilter(FSMagreeToRules))
async def cbq_agree_to_rules(callback: CallbackQuery, state: FSMContext):
    status_sender, response_sender = await Misc.post_tg_user(callback.from_user)
    if status_sender != 200:
        await callback.answer(Misc.MSG_ERROR_API, show_alert=True)
        return
    await Misc.show_card(
        profile=response_sender,
        profile_sender=response_sender,
        tg_user_sender=callback.from_user,
    )
    await state.clear()
    await callback.answer()
