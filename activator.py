import logging
import re
from urllib.parse import urlparse, parse_qsl

from telethon.tl.types import MessageEntityTextUrl, KeyboardButtonUrl, Message
from tgchequeman import exceptions, activate_multicheque, parse_url

from .. import loader

logger = logging.getLogger(__name__)

url_regex = r"([https?:\/\/]?(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+[" \
            r"^\s]{1,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[a-zA-Z0-9]+[^\s]{1,}|www\.[a-zA-Z0-9]+\.[" \
            r"a-zA-Z0-9]+[^\s]{1,})"


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

    @loader.tag("only_messages")
    async def watcher(self, message: Message):
        logger.info("event works")
        raw_message = message.message
        entity = await self.client.get_entity(message.peer_id)
        group_id = entity.username if hasattr(entity, "username") and entity.username is not None else f"c/{entity.id}"

        if group_id.lower() == "slivacheques":
            logger.info("a wild message just appeared")

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

                        bot = url.path.removeprefix("/").lower()

                        if bot == "tonrocketbot":
                            if "start" in query:
                                cheque_url = parse_url(raw_url)
                                await self.activate(cheque_url)
                except:
                    continue
