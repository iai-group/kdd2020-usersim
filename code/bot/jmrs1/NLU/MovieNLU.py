"""
Copyright (c) 2019 Uber Technologies, Inc.

Licensed under the Uber Non-Commercial License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at the root directory of this project. 

See the License for the specific language governing permissions and
limitations under the License.
"""

__author__ = "Alexandros Papangelis"

from code.bot.jmrs1.Dialogue.Action import DialogueAct, DialogueActItem, Operator
from code.bot.jmrs1.Domain.Ontology import Ontology
from code.bot.jmrs1.Domain.DataBase import DataBase, SQLDataBase, JSONDataBase

import string
import re

"""
DummyNLU is a basic implementation of NLU designed to work for Slot-Filling 
applications. The purpose of this class is to provide a quick way of running 
Conversational Agents, sanity checks, and to aid debugging.
"""


class MovieNLU():
    def __init__(self, args):
        """
        Load the ontology and database, create some patterns, and preprocess
        the database so that we avoid some computations at runtime.

        :param args:
        """
        super(MovieNLU, self).__init__()

        self.ontology = None
        self.database = None
        self.requestable_only_slots = None
        self.slot_values = None
        
        if 'ontology' not in args:
            raise AttributeError('MovieNLU: Please provide ontology!')
        if 'database' not in args:
            raise AttributeError('MovieNLU: Please provide database!')

        ontology = args['ontology']
        database = args['database']

        if isinstance(ontology, Ontology):
            self.ontology = ontology
        elif isinstance(ontology, str):
            self.ontology = Ontology(ontology)
        else:
            raise ValueError('Unacceptable ontology type %s ' % ontology)

        if database:
            if isinstance(database, DataBase):
                self.database = database

            elif isinstance(database, str):
                if database[-3:] == '.db':
                    self.database = SQLDataBase(database)
                elif database[-5:] == '.json':
                    self.database = JSONDataBase(database)
                else:
                    raise ValueError('Unacceptable database type %s '
                                     % database)
            else:
                raise ValueError('Unacceptable database type %s ' % database)

        # In order to work for simulated users, we need access to possible
        # values of requestable slots
        cursor = self.database.SQL_connection.cursor()

        print('MovieNLU: Preprocessing Database...')

        # Get table name
        db_result = cursor.execute("select * from sqlite_master "
                                   "where type = 'table';").fetchall()
        if db_result and db_result[0] and db_result[0][1]:
            db_table_name = db_result[0][1]

            self.slot_values = {}

            # Get all entries in the database
            all_items = cursor.execute("select * from " +
                                       db_table_name + ";").fetchall()

            i = 0

            for item in all_items:
                # Get column names
                slot_names = [i[0] for i in cursor.description]

                result = dict(zip(slot_names, item))

                for slot in result:
                    if slot in ['id']:
                        continue

                    if slot not in self.slot_values:
                        self.slot_values[slot] = []
                    
                    if slot in ['actors', 'genres', 'plot_keywords']:
                        temp_result = [x.strip() for x in result[slot].split(',')]
                        temp_result = temp_result[:-1] + [x.strip() for x in temp_result[-1].split(' and ')]
                        for val in temp_result:
                            if val not in self.slot_values[slot]:
                                self.slot_values[slot].append(val)
                        continue

                    if result[slot] not in self.slot_values[slot]:
                        self.slot_values[slot].append(result[slot])

                i += 1
                if i % 2000 == 0:
                    print(f'{float(i/len(all_items))*100}% done')
            print('MovieNLU: Done!')
        else:
            raise ValueError(
                'Dialogue Manager cannot specify Table Name from database '
                '{0}'.format(self.database.db_file_name))

        # For this DummyNLU create a list of requestable-only to reduce
        # computational load
        self.requestable_only_slots = \
            [slot for slot in self.ontology.ontology['requestable']
             if slot not in self.ontology.ontology['informable']] + ['name']

        self.bye_pattern = ['bye', 'goodbye', 'exit', 'quit', 'stop']

        self.thanks_pattern = ['thanks', 'thankyou', 'thank']

        self.dontlike_pattern = ['something else', 'anything else', 'dont like it', 'not this', 'another']

        self.watched_pattern = ['watched', 'seen']

        self.deny_pattern = ['no', 'nope', 'nah', 'not']

        self.affirm_pattern = ['yes', 'sure']

        self.dontcare_pattern = ['anything', 'any', 'i do not care',
                                 'i dont care', 'dont care', 'dontcare',
                                 'it does not matter', 'it doesnt matter',
                                 'does not matter', 'doesnt matter']

        punctuation = string.punctuation.replace('$', '')
        punctuation = punctuation.replace('_', '')
        punctuation = punctuation.replace('.', '')
        punctuation = punctuation.replace('&', '')
        punctuation = punctuation.replace('-', '')
        punctuation += '.'
        self.punctuation_remover = str.maketrans('', '', punctuation)

    def initialize(self, args):
        """
        Nothing to do here.

        :param args:
        :return:
        """
        pass

    def raw_utterance(self, utterance, last_sys_act):
        utterance = utterance.rstrip().lower()
        utterance = utterance.translate(self.punctuation_remover)
        if last_sys_act and last_sys_act.intent == 'offer':
            for p in self.deny_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    utterance = utterance + ' genres'
        utterance = utterance + ' '
        if 'director name' in utterance:
            utterance = utterance.replace('director name', 'director_name')
        else:
            utterance = utterance.replace('director ', 'director_name')
            utterance = utterance.replace('directors', 'director_name')
            utterance = utterance.replace('directed', 'director_name')
        if 'imdb score' in utterance:
            utterance = utterance.replace('imdb score', 'imdb_score')
        elif 'score' in utterance:
            utterance = utterance.replace('score', 'imdb_score')
        elif 'imdb' in utterance:
            utterance = utterance.replace('imdb', 'imdb_score')
        else:
            utterance = utterance.replace('rating', 'imdb_score')
        utterance = utterance.replace('genre ', 'genres ')
        utterance = utterance.replace('moive ', 'genres ')
        utterance = utterance.replace('moives', 'genres')
        utterance = utterance.replace('plot ', 'plot_keywords')
        if 'more' in utterance:
            utterance = utterance.replace('more', 'plot_keywords')
        elif 'about' in utterance:
            utterance = utterance.replace('about', 'plot_keywords')
        elif 'storyline' in utterance:
            utterance = utterance.replace('storyline', 'plot_keywords')
        utterance = utterance.replace('actor names', 'actors')
        utterance = utterance.replace('acted', 'actors')
        utterance = utterance.replace('actor ', 'actors ')
        utterance = utterance.replace('stars', 'actors')
        utterance = utterance.replace('star', 'actors')
        utterance = utterance.replace('released', 'title_year')
        utterance = utterance.replace('release', 'title_year')
        utterance = utterance.replace('year', 'title_year')
        utterance = utterance.replace('long', 'duration')
        return utterance.strip()

    def process_input(self, utterance, dialogue_state=None, dialogue_context=None):
        """
        Process the utterance and see if any intent pattern matches.

        :param utterance: a string, the utterance to be recognised
        :param dialogue_state: the current dialogue state, if available
        :return: a list of recognised dialogue acts
        """
        #print("utterance = {}, dialogue_state = {}".format(utterance, dialogue_state))
        dacts = []
        dact = DialogueAct('UNK', [])

        #extra step: convert it to string if list
        if isinstance(utterance, list):
            utterance = str(utterance)

        if not utterance:
            self.prev_dact = [dact]
            return [dact]

        last_sys_act = \
            dialogue_state.last_sys_acts[0] \
            if dialogue_state and dialogue_state.last_sys_acts else None

        if last_sys_act and (last_sys_act.intent == 'ack_feedback' or last_sys_act.intent == 'canthelp'):
            last_sys_act = dialogue_state.last_sys_acts[1]
     
        if last_sys_act and last_sys_act.intent == 'feedback':
            pass
        else:
            utterance = self.raw_utterance(utterance, last_sys_act)

        # Check for dialogue ending
        if dact.intent == 'UNK' and re.search(r'\b{0}\b'.format('help'), utterance):
            dact.intent = 'help'
            return [dact]

        if dact.intent == 'UNK':
            for p in self.thanks_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    dact.intent = 'moreinfo'
                    return [dact]

        #Check if the recommended movie is watched by the user or does not like this recommendation
        if last_sys_act and last_sys_act.intent == 'offer':
            for p in self.affirm_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    for param in last_sys_act.params:
                        if param.slot in dialogue_context.params:
                            dialogue_context.update_offer(param.slot, param.value, 'watched it')
                    dact.intent = 'feedback'
                    dact.params = []
                    for lsa_param in last_sys_act.params:
                        if lsa_param.slot == 'name' and lsa_param.value:
                            dact.params.append(lsa_param)
                            return [dact]

        if last_sys_act and dialogue_state.system_made_offer and last_sys_act.intent != 'feedback':
            for p in self.watched_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    for param in last_sys_act.params:
                        if param.slot in dialogue_context.params:
                            dialogue_context.update_offer(param.slot, param.value, 'watched it')
                    dact.intent = 'feedback'
                    dact.params = []
                    for lsa_param in last_sys_act.params:
                        if lsa_param.slot == 'name' and lsa_param.value:
                            dact.params.append(lsa_param)
                            return [dact]
            for p in self.dontlike_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    for param in last_sys_act.params:
                        if param.slot in dialogue_context.params:
                            dialogue_context.update_offer(param.slot, param.value, 'don\'t like')
                    return self.prev_dact

        #Check if the user is giving feedback on the movie
        if last_sys_act and last_sys_act.intent == 'feedback':
            for param in last_sys_act.params:
                if param.slot == 'name':
                    dact.intent = 'feedback_given'
                    dact.params.append(DialogueActItem(param.value, Operator.EQ, utterance))
                    dacts.append(dact)
                    break
            dacts.extend(self.prev_dact)
            return dacts
        
        # First check if the user doesn't care
        if (last_sys_act and last_sys_act.intent == 'request') or not last_sys_act:
            for p in self.dontcare_pattern:
                # Look for exact matches here only (i.e. user just says
                # 'i don't care')
                if p == utterance:
                    dact.intent = 'offer'
                    dact.params.append(
                        DialogueActItem(
                            last_sys_act.params[0].slot,
                            Operator.EQ,
                            'dontcare'))
                    self.prev_dact = [dact]
                    return [dact]

        # Look for slot keyword and corresponding value
        words = utterance.split(' ')

        if dact.intent == 'UNK':
            for p in self.affirm_pattern:
                if p == utterance:
                    dact.intent = 'affirm'
                    break

        # Check for dialogue ending
        if dact.intent == 'UNK':
            for p in self.bye_pattern:
                match = re.search(r'\b{0}\b'.format(p), utterance)
                if match:
                    dact.intent = 'bye'
                    break
            
        if dact.intent == 'UNK':
            dact.intent = 'inform'
            # Check if there is no information about the slot
            if 'no info' in utterance:
                # Search for a slot name in the utterance
                for slot in self.ontology.ontology['requestable']:
                    if slot in utterance:
                        dact.params.append(
                            DialogueActItem(slot, Operator.EQ, 'no info'))
                        self.prev_dact = [dact]
                        return [dact]

                # Else try to grab slot name from the other agent's
                # previous act
                if last_sys_act and \
                        last_sys_act.intent in ['request']:
                    dact.params.append(
                        DialogueActItem(
                            last_sys_act.params[0].slot,
                            Operator.EQ,
                            'dontcare'))
                    self.prev_dact = [dact]
                    return [dact]

                # Else do nothing, and see if anything matches below
        
        if dact.intent in ['inform', 'request']:
            for word in words:
                # Check for requests. Requests for informable slots are
                # captured below
                if word in self.requestable_only_slots:
                    if dact.intent == 'request':
                        dact.params.append(
                            DialogueActItem(word, Operator.EQ, ''))
                        break

                    elif word != 'name':
                        dact.intent = 'request'
                        dact.params.append(
                            DialogueActItem(word, Operator.EQ, ''))
                        break

                        # For any other kind of intent, we have no way of
                        # determining the slot's value, since such
                        # information is not in the ontology.

                # Check for informs (most intensive)
                if word in self.ontology.ontology['informable']:

                    # If a request intent has already been recognized,
                    # do not search for slot values
                    if dact.intent == 'request':
                        dact.params.append(
                            DialogueActItem(word, Operator.EQ, ''))
                        break

                    found = False

                    for p in self.ontology.ontology['informable'][word]:
                        match = re.search(r'\b{0}\b'.format(p), utterance)
                        if match:
                            if word == 'name':
                                dact.intent = 'offer'
                            else:
                                dact.intent = 'inform'

                            dact.params.append(
                                DialogueActItem(word, Operator.EQ, p))
                            found = True
                            break
                    
                    if not found:
                        # Search for dontcare (e.g. I want any area)
                        for p in self.dontcare_pattern:
                            match = re.search(r'\b{0}\b'.format(p), utterance)
                            if match:
                                dact.intent = 'inform'
                                dact.params.append(
                                    DialogueActItem(
                                        word,
                                        Operator.EQ,
                                        'dontcare'))
                                self.prev_dact = [dact]
                                return [dact]

                        dact.intent = 'request'
                        dact.params.append(
                            DialogueActItem(word, Operator.EQ, ''))
            if last_sys_act and last_sys_act.intent == 'offer':
                for param in last_sys_act.params:
                    if param.slot in dialogue_context.params:
                        if dact.intent in ['request', 'inform']:
                            dialogue_context.update_offer(param.slot, param.value, 'Acknowledged')
                        else:
                            dialogue_context.update_offer(param.slot, param.value, 'Ignored')
                        break
        # If nothing was recognised, do an even more brute-force search
        
        if dact.intent in ['UNK', 'inform'] and not dact.params:
            #print('DEBUG1 => intent is ' + dact.intent + ' for utterance ' + utterance)
            slot_vals = self.ontology.ontology['informable']
            if self.slot_values:
                slot_vals = self.slot_values
            for slot in slot_vals:
                for value in slot_vals[slot]:
                    if value and \
                            value.lower().translate(self.punctuation_remover) \
                            in utterance:
                        if slot in self.ontology.ontology['informable'] and slot != 'name':
                            dact.intent = 'offer'

                            di = DialogueActItem(slot, Operator.EQ, value)

                            if di not in dact.params:
                                dact.params.append(di)
        
        # Check if something has been missed (e.g. utterance is dont care and
        # there's no previous sys act)
        if dact.intent == 'inform':
            # Check to see that all slots have an identified value
            if dact.params:
                for dact_item in dact.params:
                    if not dact_item.slot or not dact_item.value:
                        dact.params.remove(dact_item)

                        if not dact.params:
                            dact.intent = 'UNK'
                            break

                    # Else, break up the inform into several acts
                    elif dact_item.slot == 'name':
                        dacts.append(DialogueAct('offer', [dact_item]))
                    else:
                        dacts.append(DialogueAct('inform', [dact_item]))
            else:
                dact.intent = 'canthelp'
                if last_sys_act:
                    param = DialogueActItem('',Operator.EQ,'')
                    if last_sys_act.intent == 'request':
                        for lsparam in last_sys_act.params:
                            if lsparam.slot in self.ontology.ontology['system_requestable']:
                                param.slot = lsparam.slot
                                param.value = ' | '.join(self.slot_values[lsparam.slot])
                    dact.params.append(param)
                return [dact]
        else:
            dacts.append(dact)

        for dact in dacts:
            if dact.intent == 'offer':
                self.prev_dact = dacts
                break
        return dacts

    def train(self, data):
        """
        Nothing to train.

        :param data:
        :return:
        """
        pass

    def save(self, path=None):
        """
        Nothing to save.

        :param path:
        :return:
        """
        pass

    def load(self, path):
        """
        Nothing to load.

        :param path:
        :return:
        """
        pass
