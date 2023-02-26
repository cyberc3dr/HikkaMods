import logging

from telethon.tl.custom import InlineResult
from telethon.tl.types import Message, BotInlineMessageText, MessageEntityTextUrl
from telethon.tl.custom.inlineresults import InlineResults

from .. import loader

from urllib.parse import urlparse, parse_qsl
import re

logger = logging.getLogger(__name__)

cheques = []

rocket_valid: list = [
    "mc", "mci", "t"
]

valid_bots = [
    "tonrocketbot", "cryptobot", "xjetswapbot", "wallet"
]

bots: dict = {
    5014831088: {
        "name": "TonRocket",
        "username": "tonRocketBot"
    },
    1559501630: {
        "name": "CryptoBot",
        "username": "CryptoBot"
    },
    5794061503: {
        "name": "xJetSwap",
        "username": "xJetSwapBot"
    },
    1985737506: {
        "name": "Wallet",
        "username": "wallet"
    }
}


def parse_url(s: str):
    s = s.strip("/")
    if s.startswith("://"):
        return urlparse(s[1:])
    elif not re.match("[a-zA-Z]+://.*", s):
        return urlparse("//" + s)
    return urlparse(s)


def filter_cheques(bot: str, cheque: str) -> bool:
    if bot == "tonrocketbot" and "_" in cheque:
        logger.info("TonRocket")
        split = cheque.split("_")
        cheque_type = split[0].lower()
        cheque_hash = split[1]
        if len(cheque_hash) == 15 and cheque_type in rocket_valid and cheque not in cheques:
            logger.info("rocket cheque is valid")
            cheques.append(cheque)
            return True
    elif bot == "cryptobot":
        logger.info("CryptoBot")
        if cheque.startswith("CQ") and len(cheque) == 12 and cheque not in cheques:
            logger.info("cryptobot cheque is valid")
            cheques.append(cheque)
            return True
    elif bot == "xjetswapbot":
        logger.info("xJetSwap")
        if cheque.startswith("c_") and len(cheque) == 26 and cheque not in cheques:
            logger.info("xjetswap cheque is valid")
            cheques.append(cheque)
            return True
    elif bot == "wallet":
        if cheque.startswith("C-") and len(cheque) == 12 and cheque not in cheques:
            logger.info("wallet cheque is valid")
            cheques.append(cheque)
            return True

    return False


@loader.tds
class ChequesModule(loader.Module):
    """Just for testing purposes"""

    url_regex = r"([https?:\/\/]?(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,})"

    strings = {
        "name": "ChequesMod",
        "transfer_found": "transfer found",
        "source": "Source"
    }

    strings_ru = {
        "name": "ChequesMod",
        "transfer_found": "перевод был найден",
        "source": "Источник"
    }

    def __init__(self):
        logger.info("hello from testmod")

    @loader.tag("only_messages", "in")
    async def watcher(self, message: Message):
        bot_id = message.via_bot_id

        group_id = list(message.peer_id.to_dict().values())[1]
        message_id = message.id

        bot = bots[bot_id] if bot_id in bots else None

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

                    bot_name = bot["name"]
                    bot_username = bot["username"]

                    results: InlineResults = await self.client.inline_query(bot_username, cheque)

                    if len(results) == 1:
                        inline: InlineResult = results[0]

                        from_inline_message: BotInlineMessageText = inline.message

                        button = from_inline_message.reply_markup.rows[0].buttons[0]

                        in_inline_title = inline.title
                        in_inline_description = inline.description

                        url = parse_url(button.url)
                        query = dict(parse_qsl(url.query))

                        if "start" in query:
                            logger.info("second start is valid")
                            cheque: str = query["start"]

                            if filter_cheques(bot_url, cheque):
                                logger.info("verified")

                                transfer_found = self.strings["transfer_found"]
                                source = self.strings["source"]

                                await self.inline.form(
                                    text=f"<b>{bot_name}</b> {transfer_found}\n{in_inline_title}\n{in_inline_description}\n\n{from_inline_message.message}",
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

            gen = (parse_url(url) for url in urls)
            for url in gen:
                address = url.netloc.lower()

                if address == "t.me":
                    logger.info("address valid")
                    bot_url = url.path.removeprefix("/")
                    query = dict(parse_qsl(url.query))

                    if bot_url.lower() in valid_bots:
                        if "start" in query:
                            logger.info("first start is valid")
                            cheque: str = query["start"]

                            results: InlineResults = await self.client.inline_query(bot_url, cheque)

                            if len(results) == 1:
                                inline: InlineResult = results[0]

                                from_inline_message: BotInlineMessageText = inline.message

                                button = from_inline_message.reply_markup.rows[0].buttons[0]

                                in_inline_title = inline.title
                                in_inline_description = inline.description

                                url = parse_url(button.url)
                                query = dict(parse_qsl(url.query))

                                if "start" in query:
                                    logger.info("second start is valid")
                                    cheque: str = query["start"]

                                    if filter_cheques(bot_url.lower(), cheque):
                                        logger.info("verified")

                                        transfer_found = self.strings["transfer_found"]
                                        source = self.strings["source"]

                                        await self.inline.form(
                                            text=f"<b>{bot_url}</b> {transfer_found}\n{in_inline_title}\n{in_inline_description}\n\n{from_inline_message.message}",
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


