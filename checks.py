import logging

from telethon.tl.types import Message, BotInlineMessageText
from telethon.tl.custom.inlineresults import InlineResults

from .. import loader

from urllib.parse import urlparse, parse_qsl
import re

logger = logging.getLogger(__name__)

messages = []

rocket_valid: list = [
    "mc", "mci", "t"
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


def filter_cheques(bot: str, cheque: str, raw_message: str) -> bool:
    if bot == "tonrocketbot" and "_" in cheque:
        logger.info("TonRocket")
        split = cheque.split("_")
        cheque_type = split[0].lower()
        cheque_hash = split[1]
        if len(cheque_hash) == 15 and cheque_type in rocket_valid and raw_message not in messages:
            logger.info("rocket cheque is valid")
            messages.append(raw_message)
            return True
    elif bot == "cryptobot":
        logger.info("CryptoBot")
        if cheque.startswith("CQ") and len(cheque) == 12 and raw_message not in messages:
            logger.info("cryptobot cheque is valid")
            messages.append(raw_message)
            return True
    elif bot == "xjetswapbot":
        logger.info("xJetSwap")
        if cheque.startswith("c_") and len(cheque) == 26 and raw_message not in messages:
            logger.info("xjetswap cheque is valid")
            messages.append(raw_message)
            return True
    elif bot == "wallet":
        if cheque.startswith("C-") and len(cheque) == 12 and raw_message not in messages:
            logger.info("wallet cheque is valid")
            messages.append(raw_message)
            return True

    return False


@loader.tds
class ChequesModule(loader.Module):
    """Just for testing purposes"""

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
        raw_message = message.message

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
                        result: BotInlineMessageText = results[0].message

                        button = result.reply_markup.rows[0].buttons[0]

                        message = result.message

                        url = parse_url(button.url)
                        query = dict(parse_qsl(url.query))

                        if "start" in query:
                            logger.info("second start is valid")
                            cheque: str = query["start"]

                            if filter_cheques(bot_url, cheque, message):
                                logger.info("verified")

                                transfer_found = self.strings["transfer_found"]
                                source = self.strings["source"]

                                await self.inline.form(
                                    text=f"<b>{bot_name}</b> {transfer_found}\n\n{result.message}",
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
