import logging
import re
from urllib.parse import urlparse, parse_qsl

from telethon import types
from telethon.tl.patched import Message as mmmm
from telethon.tl.types import MessageEntityTextUrl, KeyboardButtonUrl
from tgchequeman import exceptions, activate_multicheque, parse_url

from .. import loader, utils
from ..tl_cache import CustomTelegramClient

logger = logging.getLogger(__name__)

container_id = 1744074313


def parse_raw_url(s: str):
    s = s.strip("/")
    if s.startswith("://"):
        return urlparse(s[1:])
    elif not re.match("[a-zA-Z]+://.*", s):
        return urlparse("//" + s)
    return urlparse(s)


@loader.tds
class TonRocketCatcherMod(loader.Module):
    """TonRocket-Catcher"""

    strings = {"name": "TonRocket-Catcher"}
    strings_ru = {"_cls_doc": "TonRocket-Catcher"}
    tonrocketbot_id = 5014831088
    patterns = {
        "receive": r"Receive|Получить",
        "url": r"https://t\.me/tonRocketBot\?start=[^\s]+",
    }

    async def client_ready(self, client, db) -> None:
        self.client: CustomTelegramClient = client

    async def trcinfocmd(self, message: types.Message):
        """ Проверка работоспособности модуля """
        await utils.answer(message, "Все работает!")

    async def activate(self, url: dict):
        try:
            await activate_multicheque(self.client, url, '')
        except (exceptions.ChequeFullyActivatedOrNotFound, exceptions.PasswordError) as err:
            logger.error(err)
        except (exceptions.ChequeActivated,
                exceptions.ChequeForPremiumUsersOnly,
                exceptions.CannotActivateOwnCheque) as warn:
            logger.warning(warn)
            return
        except exceptions.UnknownError as err:
            logger.error(err)
            return
        except exceptions.Success:
            return
        except Exception as err:
            logger.error(err)

    @loader.tag("only_messages", chat_id=container_id)
    async def watcher(self, message: types.Message) -> None:
        logger.info("a wild message just appeared")

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

        urls = [i if i.startswith("http") else f"https://{i}" for i in urls]

        for raw_url in urls:
            url = parse_raw_url(raw_url)
            try:
                address = url.netloc.lower()

                if address == "t.me":
                    logger.info("address valid")
                    query = dict(parse_qsl(url.query))

                    bot = url.path.removeprefix("/")

                    if bot == "tonRocketBot":
                        if "start" in query:
                            cheque_url = parse_url(raw_url)
                            await self.activate(cheque_url)
            except:
                continue
