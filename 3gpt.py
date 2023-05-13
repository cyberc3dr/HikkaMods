import logging

from telethon.tl.types import Message

from gpt4free import theb, usesless

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class GPT4Free(loader.Module):
    """ChatGPT free of charge."""

    message_id = ""

    strings = {
        "name": "GPT4Free"
    }

    strings_ru = {
        "name": "GPT4Free"
    }

    @loader.command()
    async def bai(self, message: Message):
        prompt = utils.get_args_raw(message)
        if prompt:
            await utils.answer(message, f"<b>Ваш вопрос к bai</b>: {prompt}\n<b>Ответ нейросети</b>: "
                                        f"<code>Ждём...</code>")

            answer = ""

            n = 0

            while answer.strip() == "":
                n += 1
                await utils.answer(message, f"<b>Ваш вопрос к bai</b>: {prompt}\n<b>Ответ нейросети</b>: "
                                            f"<code>Ждём...{n}</code>")
                answer = theb.Completion.get_response(prompt)

            await utils.answer(message, f"<b>Ваш вопрос к bai</b>: {prompt}\n<b>Ответ нейросети</b>: {answer}")

    @loader.command()
    async def newul(self, message: Message):
        self.message_id = ""
        await utils.answer(message, "Контекст был сброшен")

    @loader.command()
    async def ul(self, message: Message):
        prompt = utils.get_args_raw(message)
        if prompt:
            await utils.answer(message, f"<b>Ваш вопрос к usesless</b>: {prompt}\n<b>Ответ нейросети</b>: "
                                        f"<code>Ждём...</code>")

            try:
                answer = usesless.Completion.create(prompt=prompt,
                                                    parentMessageId=self.message_id)

                text = answer["text"]
                self.message_id = answer["id"]

                await utils.answer(message, f"<b>Ваш вопрос к usesless</b>: {prompt}\n<b>Ответ нейросети</b>: {text}")
            except IndexError:
                await utils.answer(message, f"<b>Ваш вопрос к usesless</b>: {prompt}\n<b>Ответ нейросети</b>: "
                                            f"<code>🚫 Ошибка</code>")

    # @loader.command()
    # async def createchat(self, message: Message):
    #     args = utils.get_args(message)
    #     if args and len(args) > 0:
    #         _chat_name = args[0]
    #         chats[_chat_name] = []
    #         await utils.answer(message, f"Чат {_chat_name} был успешно создан.")
    #     else:
    #         await utils.answer(message, f"Укажите название чата в аргументе команды.")
    #
    # @loader.command()
    # async def delchat(self, message: Message):
    #     args = utils.get_args(message)
    #     if args and len(args) > 1:
    #         _chat_name = args[0]
    #         if args[0] in chats:
    #             chats.pop(args)
    #             await utils.answer(message, f"Чат {_chat_name} был успешно удалён.")
    #         else:
    #             await utils.answer(message, f"Такого чата не существует.")
    #     else:
    #         await utils.answer(message, f"Введите название чата.")
    #
    # @loader.command()
    # async def lschat(self, message: Message):
    #     await utils.answer(message, "Список чатов:\n" + "\n".join(chats.keys()))
