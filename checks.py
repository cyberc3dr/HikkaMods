import logging
import re
from abc import ABC, abstractmethod
from numbers import Number
from urllib.parse import urlparse, parse_qsl

from telethon.tl.custom import InlineResult
from telethon.tl.custom.inlineresults import InlineResults
from telethon.tl.types import Message, BotInlineMessageText, MessageEntityTextUrl, KeyboardButtonUrl

from .. import loader, utils

logger = logging.getLogger(__name__)

container_id = 1702836252

url_regex = r"([https?:\/\/]?(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[" \
            r"^\s]{1,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[" \
            r"a-zA-Z0-9]+[^\s]{1,})"


class Bot(ABC):
    cheques = []
    garbageCount = 0

    def __init__(self, id: Number, username: str, display_name: str, icon: str):
        self.id = id
        self.username = username
        self.display_name = display_name
        self.icon = icon

    def is_valid(self, cheque: str, raw_message) -> bool:
        if cheque not in self.cheques:
            _valid = self._is_valid_impl(cheque, raw_message)
            if _valid:
                self.cheques.append(cheque)
                return True
            
        self.garbageCount += 1
        return False

    @abstractmethod
    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        pass

    @property
    def supports_inline(self) -> bool:
        raise NotImplementedError


class RocketBot(Bot):
    supports_inline = True

    _rocket_valid: list = [
        "mc", "mci", "t"
    ]

    def __init__(self):
        super().__init__(5014831088, "tonRocketBot", "TonRocket", "🚀")

    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        if "_" in cheque:
            split = cheque.split("_")
            cheque_type = split[0].lower()
            cheque_hash = split[1]
            if len(cheque_hash) == 15 and cheque_type in self._rocket_valid:
                logger.info("rocket cheque is valid")
                return True
            return False


class CryptoBot(Bot):
    supports_inline = False

    def __init__(self):
        super().__init__(1559501630, "CryptoBot", "CryptoBot", "💎")

    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        if cheque.startswith("CQ") and len(cheque) == 12:
            logger.info("cryptobot cheque is valid")
            return True


class XJetSwap(Bot):
    supports_inline = True

    def __init__(self):
        super().__init__(5794061503, "xJetSwapBot", "xJetSwap", "✈️")

    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        if cheque.startswith("c_") and len(cheque) == 26:
            logger.info("xjetswap cheque is valid")
            return True


class Jetton(Bot):
    supports_inline = True

    def __init__(self):
        super().__init__(5822742440, "jetton", "Jetton", "🎰")

    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        if cheque.startswith("c_") and len(cheque) == 26:
            logger.info("jetton cheque is valid")
            return True


class Wallet(Bot):
    supports_inline = True

    def __init__(self):
        super().__init__(1985737506, "wallet", "Wallet", "💵")

    def _is_valid_impl(self, cheque: str, raw_message) -> bool:
        if cheque.startswith("C-") and len(cheque) == 12:
            logger.info("wallet cheque is valid")
            return True


# class JTonBot(Bot):
#     supports_inline = False
#     _messages = []
#
#     def __init__(self):
#         super().__init__(5500608060, "jtonbot", "JTON Wallet", "⚫️")
#
#     def _is_valid_impl(self, cheque: str, raw_message) -> bool:
#         if raw_message is not None:
#             message = re.sub(r'\([^()]*\)', '', raw_message)
#             message = re.sub(url_regex, '', message)
#             message = "\n".join([i for i in message.split("\n") if not i.startswith("Активаций: ")])
#             if message not in self._messages:
#                 self._messages.append(message)
#             else:
#                 return False
#
#         if cheque.startswith("cr_") and len(cheque) == 14:
#             logger.info("jton cheque is valid")
#             return True


class BotRegistry:
    bots: list[Bot] = [
        RocketBot(),
        CryptoBot(),
        XJetSwap(),
        Wallet(),
        # JTonBot(),
        Jetton()
    ]

    def get_by_id(self, id: Number):
        if id is not None:
            for bot in self.bots:
                if bot.id == id:
                    return bot
        return None

    def get_by_username(self, username: str):
        if username is not None:
            for bot in self.bots:
                if bot.username == username:
                    return bot
        return None


registry = BotRegistry()


def parse_url(s: str):
    s = s.strip("/")
    if s.startswith("://"):
        return urlparse(s[1:])
    elif not re.match("[a-zA-Z]+://.*", s):
        return urlparse("//" + s)
    return urlparse(s)


@loader.tds
class ChequesModule(loader.Module):
    """Just for testing purposes"""

    strings = {
        "name": "ChequesMod",
        "transfer_found": "transfer found",
        "source": "Source",
        "activate": "Activate",
        "message_hidden": "Message hidden.",
        "bot_not_inline": "Bot doesn't support inline.",
        "total": "Total cheques",
        "garbage": "Garbage cheques"
    }

    strings_ru = {
        "name": "ChequesMod",
        "transfer_found": "перевод был найден",
        "source": "Источник",
        "activate": "Активировать",
        "message_hidden": "Сообщение скрыто",
        "bot_not_inline": "Бот не поддерживает inline.",
        "total": "Всего чеков",
        "garbage": "Мусорных чеков"
    }

    def __init__(self):
        logger.info("hello from testmod")

    @loader.command(ru_doc="Проверить состояние контейнера", en_doc="Check container")
    async def cqstats(self, message: Message):
        _result = "<b>Статистика: </b>\n\n"
        for bot in registry.bots:
            _result += f"{bot.icon} <b>{bot.display_name}:</b>\n"
            _result += f"<b>{self.strings['total']}:</b> <code>{len(bot.cheques)}</code>\n"
            _result += f"<b>{self.strings['garbage']}:</b> <code>{bot.garbageCount}</code>\n\n"

        await utils.answer(message, _result)

    @loader.tag("only_messages", "in")
    async def watcher(self, message: Message):
        raw_message = message.message
        entity = await self.client.get_entity(message.peer_id)
        group_id = entity.username if entity.username is not None else f"c/{entity.id}"

        message_id = message.id

        bot = registry.get_by_id(message.via_bot_id)

        if bot is not None:
            # logger.info("bot is not none")

            url = parse_url(message.reply_markup.rows[0].buttons[0].url)

            address = url.netloc.lower()

            if address == "t.me":
                # logger.info("address valid")
                query = dict(parse_qsl(url.query))

                if "start" in query:
                    # logger.info("first start is valid")
                    cheque: str = query["start"]

                    original_message = message.message
                    button = message.reply_markup.rows[0].buttons[0]

                    in_inline_title = f"\n📘 {self.strings['bot_not_inline']}"
                    in_inline_description = ""

                    if bot.supports_inline:
                        # logger.info("inline")
                        results: InlineResults = await self.client.inline_query(bot.username, cheque)

                        if len(results) == 1:
                            inline: InlineResult = results[0]

                            _message: BotInlineMessageText = inline.message
                            original_message = _message.message

                            button = _message.reply_markup.rows[0].buttons[0]

                            in_inline_title = f"\n📕 {inline.title}"
                            in_inline_description = f"\n {inline.description}"

                            url = parse_url(button.url)
                            query = dict(parse_qsl(url.query))

                            if "start" in query:
                                # logger.info("second start is valid")
                                cheque: str = query["start"]
                        else:
                            return

                    if bot.is_valid(cheque, raw_message):
                        # logger.info("verified")

                        await self.inline.form(
                            text=f"{bot.icon} <b>{bot.display_name}</b> {self.strings['transfer_found']}{in_inline_title}{in_inline_description}\n\n{original_message}",
                            message=container_id,
                            reply_markup=[
                                [
                                    {
                                        "text": bot.icon + " " + button.text.removeprefix("🌟 "),
                                        "url": button.url
                                    }
                                ],
                                [
                                    {
                                        "text": self.strings['source'],
                                        "url": f"https://t.me/{group_id}/{message_id}"
                                    }
                                ]
                            ]
                        )
        else:
            raw_message = message.message
            urls = re.findall(url_regex, raw_message)
            entities = message.entities
            if entities is not None:
                for i in entities:
                    if isinstance(i, MessageEntityTextUrl):
                        _url = i.url
                        if re.match(url_regex, _url) is not None:
                            urls.append(_url)

            reply_markup = message.reply_markup
            if reply_markup is not None:
                for row in reply_markup.rows:
                    for button in row.buttons:
                        if isinstance(button, KeyboardButtonUrl):
                            _url = button.url
                            if re.match(url_regex, _url) is not None:
                                urls.append(_url)

            urls = [*set(urls)]

            for raw_url in urls:
                url = parse_url(raw_url)
                try:
                    address = url.netloc.lower()

                    if address == "t.me":
                        # logger.info("address valid")
                        query = dict(parse_qsl(url.query))

                        bot = registry.get_by_username(url.path.removeprefix("/"))

                        if bot is not None:
                            if "start" in query:
                                # logger.info("first start is valid")
                                cheque: str = query["start"]

                                button_text = self.strings["activate"]
                                button_url = raw_url

                                original_message = f"🚫 {self.strings['message_hidden']}"
                                in_inline_title = f"\n📘 {self.strings['bot_not_inline']}"
                                in_inline_description = ""

                                if bot.supports_inline:
                                    # logger.info("inline")
                                    results: InlineResults = await self.client.inline_query(bot.username, cheque)

                                    if len(results) == 1:
                                        inline: InlineResult = results[0]

                                        from_inline_message: BotInlineMessageText = inline.message
                                        original_message = from_inline_message.message

                                        button = from_inline_message.reply_markup.rows[0].buttons[0]

                                        button_text = button.text
                                        button_url = button.url

                                        in_inline_title = f"\n📕 {inline.title}"
                                        in_inline_description = f"\n{inline.description}"

                                        url = parse_url(button.url)
                                        query = dict(parse_qsl(url.query))

                                        if "start" in query:
                                            # logger.info("second start is valid")
                                            cheque: str = query["start"]
                                    else:
                                        continue

                                button_url = button_url if button_url.startswith("http") else "https://" + button_url

                                if bot.is_valid(cheque, None):
                                    # logger.info("verified")

                                    await self.inline.form(
                                        text=f"{bot.icon} <b>{bot.display_name}</b> {self.strings['transfer_found']}{in_inline_title}{in_inline_description}\n\n{original_message}",
                                        message=container_id,
                                        reply_markup=[
                                            [
                                                {
                                                    "text": bot.icon + " " + button_text.removeprefix("🌟 "),
                                                    "url": button_url
                                                }
                                            ],
                                            [
                                                {
                                                    "text": self.strings['source'],
                                                    "url": f"https://t.me/{group_id}/{message_id}"
                                                }
                                            ]
                                        ]
                                    )
                except:
                    continue
