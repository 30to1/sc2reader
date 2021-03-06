from __future__ import absolute_import

import hashlib

from collections import namedtuple

from sc2reader.constants import *
from sc2reader.utils import PersonDict, AttributeDict

Location = namedtuple('Location',('x','y'))
Details = namedtuple('Details',['players','map','unknown1','unknown2','unknown3','file_time','utc_adjustment','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10'])

MapData = namedtuple('MapData',['unknown','gateway','map_hash'])
PlayerData = namedtuple('PlayerData',['name','bnet','race','color','unknown1','unknown2','handicap','unknown3','result'])
ColorData = namedtuple('ColorData',['a','r','g','b'])
BnetData = namedtuple('BnetData',['unknown1','unknown2','subregion','uid'])

class Team(object):
    """
    The team object primarily a container object for organizing :class:`Player`
    objects with some metadata. As such, it implements iterable and can be
    looped over like a list.

    :param interger number: The team number as recorded in the replay
    """

    #: A unique hash identifying the team of players
    hash = str()

    #: The team number as recorded in the replay
    number = int()

    #: A list of the :class:`Player` objects on the team
    players = list()

    #: The result of the game for this team.
    #: One of "Win", "Loss", or "Unknown"
    result = str()

    #: A string representation of the team play races like PP or TPZZ. Random
    #: pick races are not reflected in this string
    lineup = str()

    def __init__(self,number):
        self.number = number
        self.players = list()
        self.result = "Unknown"
        self.lineup = ""

    def __iter__(self):
        return self.players.__iter__()

    @property
    def hash(self):
        raw_hash = ','.join(sorted(p.url for p in self.players))
        return hashlib.sha256(raw_hash).hexdigest()


class Attribute(object):

    id_map = {
        0x01F4: ("Player Type", PLAYER_TYPE_CODES),
        0x07D1: ("Game Type", GAME_FORMAT_CODES),
        0x0BB8: ("Game Speed", GAME_SPEED_CODES),
        0x0BB9: ("Race", RACE_CODES),
        0x0BBA: ("Color", TEAM_COLOR_CODES),
        0x0BBB: ("Handicap", None),
        0x0BBC: ("Difficulty", DIFFICULTY_CODES),
        0x0BC1: ("Category", GAME_TYPE_CODES),
        0x07D2: ("Teams1v1", lambda value: int(value[0])),
        0x07D3: ("Teams2v2", lambda value: int(value[0])),
        0x07D4: ("Teams3v3", lambda value: int(value[0])),
        0x07D5: ("Teams4v4", lambda value: int(value[0])),
        0x07D6: ("TeamsFFA", lambda value: int(value[0])),
        0x07D7: ("Teams5v5", lambda value: int(value[0]))
    }

    def __init__(self, data):
        #Unpack the data values and add a default name of unknown to be
        #overridden by known attributes; acts as a flag for exclusion
        self.header, self.id, self.player, self.value, self.name = tuple(data+["Unknown"])

        #Strip off the null bytes
        while self.value[-1] == '\x00': self.value = self.value[:-1]

        if self.id in self.id_map:
            self.name, lookup = self.id_map[self.id]
            if lookup:
                if callable(lookup):
                    self.value = lookup(self.value)
                else:
                    self.value = lookup[self.value]

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[%s] %s: %s" % (self.player, self.name, self.value)

class Person(object):
    """
    The person object is never actually instanciated but instead acts as a
    parent class for the :class:`Observer` and :class:`Player` classes.

    :param integer pid: The person's unique id in this game.
    :param string name: The person's battle.net name
    """

    #: The person's unique in this game
    pid = int()

    #: The person's battle.net name
    name = str()

    #: A flag indicating the player's observer status.
    #: Really just a shortcut for isinstance(obj, Observer).
    is_observer = bool()

    #: A list of :class:`ChatEvent` objects representing all of the chat
    #: messages the person sent during the game
    messages = list()

    #: A list of :class:`Event` objects representing all the game events
    #: generated by the person over the course of the game
    events = list()

    #: A flag indicating if this person was the one who recorded the game.
    recorder = bool()

    #: A flag indicating if the person is a computer or human
    is_human = bool()

    def __init__(self, pid, name):
        self.pid = pid
        self.name = name
        self.is_observer = None
        self.messages = list()
        self.events = list()
        self.is_human = bool()
        self.recorder = False # Actual recorder will be determined using the replay.message.events file

class Observer(Person):
    """
    A subclass of the :class:`Person` class for observers. Fewer attributes
    are made available for observers in the replay file.

    All Observers are human.
    """
    def __init__(self, pid, name):
        super(Observer,self).__init__(pid, name)
        self.is_observer = True
        self.is_human = True

class Player(Person):
    """
    A subclass of the :class:`Person` class for players.
    """

    URL_TEMPLATE = "http://%s.battle.net/sc2/en/profile/%s/%s/%s/"

    #: A reference to the player's :class:`Team` object
    team = None

    #: A reference to a :class:`Color` object representing the player's color
    color = None

    #: The race the player picked prior to the game starting.
    #: Protoss, Terran, Zerg, Random
    pick_race = str()

    #: The race the player ultimately wound up playing.
    #: Protoss, Terran, Zerg
    play_race = str()

    #: The difficulty setting for the player. Always Medium for human players.
    #: Very easy, East, Medium, Hard, Very hard, Insane
    difficulty = str()

    #: The player's handicap as set prior to game start, ranges from 50-100
    handicap = int()

    #: The player's region
    region = str()

    #: The subregion with in the player's region
    subregion = int()

    def __init__(self, pid, name):
        super(Player,self).__init__(pid, name)
        self.is_observer = False

    @property
    def url(self):
        """The player's battle.net profile url"""
        return self.URL_TEMPLATE % (self.gateway, self.uid, self.subregion, self.name)

    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid, self.name, self.play_race)

    @property
    def result(self):
        """The game result for this player"""
        return self.team.result

    def format(self, format_string):
        return format_string.format(**self.__dict__)

    def __repr__(self):
        return str(self)
