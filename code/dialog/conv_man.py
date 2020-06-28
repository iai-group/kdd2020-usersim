"""
ConversationManager
===================

Author: Shuo Zhang, Krisztian Balog
"""

from code.user.human_user import HumanUser
# from code.bot.movie_bot import MovieBot
from code.bot.and_chill import AndChill, Botbot
from code.telegram.balog_bot import *
import json
import time
from code.bot.jmrs1.ConversationalAgent.ConversationalSingleAgent import \
    ConversationalSingleAgent
import configparser
import yaml
import sys
import os.path
import time
import random


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

    def run_single_agent(self, config, num_dialogues):
        """
        This function will create an agent and orchestrate the conversation.

        :param config: a dictionary containing settings
        :param num_dialogues: how many dialogues to run for
        :return: some statistics
        """
        ca = ConversationalSingleAgent(config)
        ca.initialize()

        print('=======================================\n')

        last_update_id = None
        while True:
            updates = self._bb.get_updates(last_update_id)
            if len(updates["result"]) > 0:
                last_update_id = self._bb.get_last_update_id(updates) + 1
                for update in updates["result"]:
                    text = update["message"]["text"]
                    chat = update["message"]["chat"]["id"]
                    self._chat = chat
                    self._history = [i for i in self._history if i[2]==self._chat]
                    self._history.append(["user", text, chat])
                    if text.lower() == "hi" or text.lower() == "hello" or text.lower() == "go":
                        system_utterance = ca.start_dialogue()
                    elif text.lower() == "code":
                        if len(self._history) < 8:
                            self._bb.send_message("You have not started your chat!", chat)
                        else:
                            self._bb.send_message("$%GVN&K<112)", chat)
                    else:
                        try:
                            system_utterance = ca.continue_dialogue(text)
                        except:
                            system_utterance = "Ok"
                    self._bb.send_message(system_utterance, chat)
                    self._history.append(["agent", system_utterance, chat])
            time.sleep(0.5)
            if self._chat:
                with open(str(self._chat)+".json", "w", encoding="utf-8") as f:
                    json.dump(self._history, f, indent=2)

def arg_parse(args=None):
    """
    This function will parse the configuration file that was provided as a
    system argument into a dictionary.

    :return: a dictionary containing the parsed config file.
    """

    cfg_parser = None

    arg_vec = args if args else sys.argv

    # Parse arguments
    if len(arg_vec) < 3: print('WARNING: No configuration file.')
    test_mode = arg_vec[1] == '-t'
    if test_mode: return {'test_mode': test_mode}

    # Initialize random seed
    random.seed(time.time())

    cfg_filename = arg_vec[2]
    if isinstance(cfg_filename, str):
        if os.path.isfile(cfg_filename):
            # Choose config parser
            parts = cfg_filename.split('.')
            if len(parts) > 1:
                if parts[1] == 'yaml':
                    with open(cfg_filename, 'r') as file:
                        cfg_parser = yaml.load(file, Loader=yaml.Loader)
                elif parts[1] == 'cfg':
                    cfg_parser = configparser.ConfigParser()
                    cfg_parser.read(cfg_filename)
                else:
                    raise ValueError('Unknown configuration file type: %s'
                                     % parts[1])
        else:
            raise FileNotFoundError('Configuration file %s not found'
                                    % cfg_filename)
    else:
        raise ValueError('Unacceptable value for configuration file name: %s '
                         % cfg_filename)

    dialogues = 10
    interaction_mode = 'simulation'

    if cfg_parser:
        dialogues = int(cfg_parser['DIALOGUE']['num_dialogues'])

        if 'interaction_mode' in cfg_parser['GENERAL']:
            interaction_mode = cfg_parser['GENERAL']['interaction_mode']

    return {'cfg_parser': cfg_parser,
            'dialogues': dialogues,
            'interaction_mode': interaction_mode}

if __name__ == "__main__":
    user = HumanUser()  # change here to use a simulated user
    bot = Botbot()
    conv_man = ConversationManager(user, bot)
    args = ['','-config', os.path.join(os.path.abspath("./.."), "kdd2020-userSim/code/bot/jmrs1/config/movies_text.yaml")]
    args = arg_parse(args)
    cfg_parser = args['cfg_parser']
    dialogues = args['dialogues']
    interaction_mode = args['interaction_mode']
    conv_man.run_single_agent(cfg_parser, dialogues)
