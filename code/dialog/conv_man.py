"""
ConversationManager
===================

Author: Shuo Zhang, Krisztian Balog
"""

from code.user.human_user import HumanUser
from code.bot.movie_bot import MovieBot
from code.bot.and_chill import AndChill, Botbot
from code.telegram.balog_bot import *
import json
import time


class ConversationManager:
    """Conversation Manager"""

    def __init__(self, user, bot):
        self._user = user
        self._bot = bot
        self._history = []  # record the chats
        self._bb = BalogBot()
        self._chat = None

    def moviebot_to_teelgram(self):
        last_update_id = None
        while True:
            updates = self._bb.get_updates(last_update_id)
            if len(updates["result"]) > 0:
                for update in updates["result"]:
                    print(last_update_id, update["message"]["text"])
                    flag = False
                    if update["message"]["text"].lower() == "stop":
                        flag = True
                last_update_id = self._bb.get_last_update_id(updates) + 1
                self.handle_updates_moviebot(updates)
                if flag:
                    break
            time.sleep(0.5)

    def handle_updates_moviebot(self, updates):
        for update in updates["result"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            self._chat = chat
            self._history = [i for i in self._history if i[2] == self._chat]
            if text == "/done":
                self._bb.send_message("Select an item to delete", chat, keyboard)
            elif text == "/start" or text.lower() == "hello" or text.lower() == "hi" or text.lower() == "go":
                self._history.append(["user", "hello", chat])
                system_utterance = self._bot.generate_response("hello")
                self._bb.send_message(system_utterance, chat)
                self._history.append(["agent", system_utterance, chat])
            elif text.lower() == "code":
                if len(self._history) < 8:
                    self._bb.send_message("You have not started your chat!", chat)
                else:
                    self._bb.send_message("$%GVN&K<)", chat)
            elif text.startswith("/"):
                continue
            elif text in items:
                self._history.append(["user", text, chat])
                system_utterance = self._bot.generate_response(text)
                self._bb.send_message(system_utterance, chat)
                self._history.append(["agent", system_utterance, chat])
            else:
                self._history.append(["user", text, chat])
                system_utterance = self._bot.generate_response(text)
                self._bb.send_message(system_utterance, chat)
                self._history.append(["agent", system_utterance, chat])

    def andchill_to_teelgram(self):
        last_update_id = None
        while True:
            updates = self._bb.get_updates(last_update_id)
            try:
                _, system_utterance, chat = self._history[-1]
                a = self._bot.fetch_last_msg(system_utterance)
            except Exception:
                a = None
            if a:
                for item in a:
                    self._bb.send_message(item, chat)
                    self._history.append(["agent", item, chat])
            if len(updates["result"]) > 0:
                last_update_id = self._bb.get_last_update_id(updates) + 1
                self.handle_updates_andchill(updates)
            time.sleep(0.5)
            if self._chat:
                with open(str(self._chat) + ".json", "w", encoding="utf-8") as f:
                    json.dump(self._history, f, indent=2)

    def handle_updates_andchill(self, updates):
        for update in updates["result"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            self._chat = chat
            self._history = [i for i in self._history if i[2] == self._chat]
            print(text)
            if text == "/done":
                print(self._history)
                # keyboard = self._bb.build_keyboard(items)
                # self._bb.send_message("Select an item to delete", chat, keyboard)
            elif text.lower() == "code":
                if len(self._history) < 8:
                    self._bb.send_message("You have not started your chat!", chat)
                else:
                    self._bb.send_message("$%GVN&K<)" + str(chat), chat)
            elif text == "/start" or text.lower() == "go":
                self._history.append(["user", "go", chat])
                system_utterance = self._bot.generate_response("go")
                self._history.append(["agent", system_utterance, chat])
                self._bb.send_message(system_utterance, chat)
            elif text.startswith("/"):
                continue
            elif text in items:
                self._history.append(["user", text, chat])
                system_utterance = self._bot.generate_response(text)
                self._history.append(["agent", system_utterance, chat])
                self._bb.send_message(system_utterance, chat)
            else:
                self._history.append(["user", text, chat])
                system_utterance = self._bot.generate_response(text)
                self._history.append(["agent", system_utterance, chat])
                self._bb.send_message(system_utterance, chat)


if __name__ == "__main__":
    user = HumanUser()  # change here to use a simulated user
    bot = MovieBot()
    conv_man = ConversationManager(user, bot)
    conv_man.moviebot_to_teelgram()

    # user = HumanUser()  # change here to use a simulated user
    # bot = AndChill()
    # conv_man = ConversationManager(user, bot)
    # conv_man.andchill_to_teelgram()
