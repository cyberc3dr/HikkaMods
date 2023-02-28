import logging
from abc import ABC, abstractmethod
from numbers import Number

from telethon.tl.custom import InlineResult
from telethon.tl.types import Message, BotInlineMessageText, MessageEntityTextUrl, KeyboardButtonUrl
from telethon.tl.custom.inlineresults import InlineResults

from .. import loader

from urllib.parse import urlparse, parse_qsl
import re

logger = logging.getLogger(__name__)

container_id = 1744074313


class Bot(ABC):
    _cheques = []

    def __init__(self, id: Number, username: str, display_name: str):
        self.id = id
        self.username = username
        self.display_name = display_name

    def is_valid(self, cheque: str) -> bool:
        if cheque in self._cheques:
            self._cheques.append(cheque)
            return self._is_valid_impl(cheque)
        return False

    @abstractmethod
    def _is_valid_impl(self, cheque: str) -> bool:
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
        super().__init__(5014831088, "tonRocketBot", "TonRocket")

    def _is_valid_impl(self, cheque: str) -> bool:
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
        super().__init__(1559501630, "CryptoBot", "CryptoBot")

    def _is_valid_impl(self, cheque: str) -> bool:
        if cheque.startswith("CQ") and len(cheque) == 12:
            logger.info("cryptobot cheque is valid")
            return True


class XJetSwap(Bot):
    supports_inline = True

    def __init__(self):
        super().__init__(5794061503, "xJetSwapBot", "xJetSwap")

    def _is_valid_impl(self, cheque: str) -> bool:
        if cheque.startswith("c_") and len(cheque) == 26:
            logger.info("xjetswap cheque is valid")
            return True


class Wallet(Bot):
    supports_inline = True

    def __init__(self):
        super().__init__(1985737506, "wallet", "Wallet")

    def _is_valid_impl(self, cheque: str) -> bool:
        if cheque.startswith("C-") and len(cheque) == 12:
            logger.info("wallet cheque is valid")
            return True


class BotRegistry:
    bots: list[Bot] = [
        RocketBot(),
        CryptoBot(),
        XJetSwap(),
        Wallet()
    ]

    def get_by_id(self, id: Number | None):
        if id is not None:
            for bot in self.bots:
                if bot.id == id:
                    return bot
        return None

    def get_by_username(self, username: str | None):
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

    url_regex = r"([https?:\/\/]?(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,})"

    strings = {
        "name": "ChequesMod",
        "transfer_found": "transfer found",
        "source": "Source",
        "activate": "Activate"
    }

    strings_ru = {
        "name": "ChequesMod",
        "transfer_found": "перевод был найден",
        "source": "Источник",
        "activate": "Активировать"
    }

    def __init__(self):
        logger.info("hello from testmod")

    @loader.tag("only_messages", "in")
    async def watcher(self, message: Message):
        group_id = list(message.peer_id.to_dict().values())[1]
        message_id = message.id

        bot = registry.get_by_id(message.via_bot_id)

        if bot is not None:
            logger.info("bot is not none")

            url = parse_url(message.reply_markup.rows[0].buttons[0].url)

            address = url.netloc.lower()

            if address == "t.me":
                logger.info("address valid")
                bot_url = url.path.removeprefix("/").lower()
                query = dict(parse_qsl(url.query))

                if "start" in query:
                    logger.info("first start is valid")
                    cheque: str = query["start"]

                    original_message = message.message
                    button = message.reply_markup.rows[0].buttons[0]

                    in_inline_title = "\nБот не поддерживает inline"
                    in_inline_description = ""

                    if bot.supports_inline:
                        logger.info("inline")
                        results: InlineResults = await self.client.inline_query(bot.username, cheque)

                        if len(results) == 1:
                            inline: InlineResult = results[0]

                            _message: BotInlineMessageText = inline.message
                            original_message = _message.message

                            button = _message.reply_markup.rows[0].buttons[0]

                            in_inline_title = "\n" + inline.title
                            in_inline_description = "\n" + inline.description

                            url = parse_url(button.url)
                            query = dict(parse_qsl(url.query))

                            if "start" in query:
                                logger.info("second start is valid")
                                cheque: str = query["start"]
                        else:
                            return

                    if bot.is_valid(cheque):
                        logger.info("verified")

                        transfer_found = self.strings["transfer_found"]
                        source = self.strings["source"]

                        await self.inline.form(
                            text=f"<b>{bot.display_name}</b> {transfer_found}{in_inline_title}{in_inline_description}\n\n{original_message}",
                            message=1744074313,
                            reply_markup=[
                                [
                                    {
                                        "text": button.text,
                                        "url": button.url
                                    },
                                    {
                                        "text": source,
                                        "url": f"https://t.me/c/{group_id}/{message_id}"
                                    }
                                ]
                            ]
                        )
        else:
            raw_message = message.message
            urls = re.findall(self.url_regex, raw_message)
            entities = message.entities
            if entities is not None:
                for i in entities:
                    if isinstance(i, MessageEntityTextUrl):
                        _url = i.url
                        if re.match(self.url_regex, _url) is not None:
                            urls.append(_url)

            reply_markup = message.reply_markup
            if reply_markup is not None:
                for row in reply_markup.rows:
                    for button in row.buttons:
                        if isinstance(button, KeyboardButtonUrl):
                            _url = button.url
                            if re.match(self.url_regex, _url) is not None:
                                urls.append(_url)

            urls = [*set(urls)]

            for raw_url in urls:
                url = parse_url(raw_url)
                try:
                    address = url.netloc.lower()

                    if address == "t.me":
                        logger.info("address valid")
                        query = dict(parse_qsl(url.query))

                        bot = registry.get_by_username(url.path.removeprefix("/"))

                        if bot is not None:
                            if "start" in query:
                                logger.info("first start is valid")
                                cheque: str = query["start"]

                                button_text = self.strings["activate"]
                                button_url = raw_url

                                original_message = "\nСообщение скрыто"
                                in_inline_title = "\nБот не поддерживает inline"
                                in_inline_description = ""

                                if bot.supports_inline:
                                    logger.info("inline")
                                    results: InlineResults = await self.client.inline_query(bot.username, cheque)

                                    if len(results) == 1:
                                        inline: InlineResult = results[0]

                                        from_inline_message: BotInlineMessageText = inline.message
                                        original_message = f"\n\n{from_inline_message.message}"

                                        button = from_inline_message.reply_markup.rows[0].buttons[0]

                                        button_text = button.text
                                        button_url = button.url

                                        in_inline_title = f"\n{inline.title}"
                                        in_inline_description = f"\n{inline.description}"

                                        url = parse_url(button.url)
                                        query = dict(parse_qsl(url.query))

                                        if "start" in query:
                                            logger.info("second start is valid")
                                            cheque: str = query["start"]
                                    else:
                                        continue

                                if bot.is_valid(cheque):
                                    logger.info("verified")

                                    transfer_found = self.strings["transfer_found"]
                                    source = self.strings["source"]

                                    await self.inline.form(
                                        text=f"<b>{bot.display_name}</b> {transfer_found}{in_inline_title}{in_inline_description}\n\n{original_message}",
                                        message=container_id,
                                        reply_markup=[
                                            [
                                                {
                                                    "text": button_text,
                                                    "url": button_url
                                                },
                                                {
                                                    "text": source,
                                                    "url": f"https://t.me/c/{group_id}/{message_id}"
                                                }
                                            ]
                                        ]
                                    )
                except:
                    continue
