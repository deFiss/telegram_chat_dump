from loguru import logger
import colorama
import time
import sys
import os
import datetime
import json
import string
import random
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.types import Message


# leaked telegram desktop app id and hash
# you can insert your
# see https://core.telegram.org/api/obtaining_api_id
APP_ID = 4
APP_HASH = "014b35b6184100b085b0d0572f9b5103"



class Dumper:
    def __init__(self):
        self.client = None
        self.messages = []
        self.chat_name = None
        self.me_user = None
        self.dump_dir_name = None

    async def dump(self):
        self.client = TelegramClient(
            "account_session",
            APP_ID,
            APP_HASH,
        )
        logger.info("Account authorization")


        await self.client.start(
                phone=self._enter_phone,
                code_callback=self._enter_code,
                password=self._enter_2fa_code,
        )

        logger.info(f"Account authorization was successful")

        # self.chat_name = input("Enter the name of the chat for the dump in the form that you see it in the list of dialogs: ")
        self.chat_name = "deFiss"

        chat_id = await self._get_chat_id(self.chat_name)
        
        logger.info(f"Chat successful found, id: {chat_id}")

        self.me_user = await self.client.get_me()

        self.dump_dir_name = self._init_dump_dir(chat_id)

        offset_id = 0

        while True:

            history = await self.client(
                GetHistoryRequest(
                    peer=chat_id,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    limit=300,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )

            time.sleep(0.3)

            if len(history.messages) == 0:
                logger.info(f"all {len(self.messages)} messages load")
                break

            logger.debug(f"load {len(history.messages)} messages")

            for m in history.messages:
                await self._process_message(m, history.users)

            offset_id = history.messages[-1].id
        

        logger.info(f"Save result to {self.dump_dir_name}")

        d = json.dumps(self.messages[::-1], indent=4, ensure_ascii=False)

        with open(os.path.join(self.dump_dir_name, "messages.json"), 'w+', encoding="utf-8") as f:
            f.write(d)


    async def _process_message(self, msg: Message, users):
        m = {}

        m["datetime"] = msg.date.strftime("%c")
        m["author"] = self._get_author_name(msg, users)
        m["text"] = msg.raw_text
    
        if msg.file:
            logger.debug("found attachment file, downloading...")
            
            f_dir = os.path.join(self.dump_dir_name, "media")
            if not os.path.exists(f_dir):
                os.mkdir(f_dir)
            
            f_name = self.randomword(16)+msg.file.ext

            await self.client.download_media(msg.media, os.path.join(f_dir, f_name))

            logger.debug(f"attachment ({f_name}) downloading done")
            
            m["attachment"] = f_name


        self.messages.append(m)

    @staticmethod
    def randomword(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    @staticmethod
    def _get_author_name(msg: Message, users):

        for u in users:
            if u.id == msg.sender_id:
                return u.first_name
            
        raise Exception("user not found")

    @staticmethod
    def _enter_code():
        return input("Enter the code from the Telegram message: ")

    @staticmethod
    def _init_dump_dir(chat_id):
        if not os.path.exists("dumps"):
                os.mkdir("dumps")

        d_name = os.path.join("dumps", f"{chat_id}_{int(time.time())}")
        os.mkdir(d_name)
        return d_name

    @staticmethod
    def _enter_phone():
        return input("Enter you telegram phone number: ")
    
    @staticmethod
    def _enter_2fa_code():
        return input("Enter your two-factor authentication password: ")


    async def _get_chat_id(self, chat_name):
        async for dialog in self.client.iter_dialogs():
            if dialog.name == chat_name:
                return dialog.id

        logger.critical(
            f"Chat with the name {chat_name} was not found in the list of conversations"
        )
        return None



async def main():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<cyan>{time}</cyan> | <lvl>{level}</lvl> - <lvl>{message}</lvl>",
        colorize=True,
        level="DEBUG",
    )

    logger.info(colorama.Fore.LIGHTYELLOW_EX + "Created by https://github.com/deFiss")

    d = Dumper()
    await d.dump()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
