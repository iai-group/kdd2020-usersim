"""
Base natural language understanding class
=========================================

Abstract class for entity linking method.

Author: Shuo Zhang, Krisztian Balog
"""

from abc import ABC, abstractmethod


class NLU(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def link_entities(self, text):
        """Links entities in the given text."""
        pass
