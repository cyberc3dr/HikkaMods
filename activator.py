import logging
import re

from telethon import types
from telethon.tl.patched import Message as mmmm
from tgchequeman import exceptions, activate_multicheque, parse_url

from .. import loader, utils
from ..tl_cache import CustomTelegramClient

logger = logging.getLogger(__name__)

container_id = 1744074313

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

    @loader.tag("only_messages", "in", chat_id=container_id)
    async def watcher(self, message: types.Message) -> None:
        # Если сообщение от имени @TonRocketBot
        if not isinstance(message, mmmm):
            return
        if message.from_id in [self.tonrocketbot_id]:
            return
        if message.via_bot_id in [self.tonrocketbot_id]:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if re.search(self.patterns['receive'], button.text):
                        url = parse_url(button.url)
                        await self.activate(url)

        elif message.message and re.search(self.patterns['url'], message.message):
            link_match = re.search(self.patterns['url'], message.message)
            url = parse_url(link_match.group())
            await self.activate(url)