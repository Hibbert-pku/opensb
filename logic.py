# encoding: utf-8
''' Core logics
'''
from collections import OrderedDict


class MemoryStatus:
    UNKNOWN = 0
    GOOD = 1
    BAD = 2
    WANTING = 3


class Config:
    max_bad = 14
    group_size = 7
    day_cap = 100
    day_new = 50
    max_mem = 3


class CoreLogic:

    know_trans = {
        MemoryStatus.UNKNOWN: MemoryStatus.GOOD,
        MemoryStatus.BAD: MemoryStatus.WANTING,
        MemoryStatus.WANTING: MemoryStatus.GOOD,
    }

    def __init__(self, wordlist, memory=None, config=None):
        self._wordlist = wordlist
        self._updated = set()  # has been marked as GOOD today

        self._memory = {word: 0 for word in self.wordlist}
        self._memory.update(memory)

        if config is None:
            config = Config()
        self.config = config

        # make daily task
        from random import shuffle
        old_words = [word for word, prof in self.memory.items()
                     if 0 < prof < self.config.max_mem]
        new_words = [word for word, prof in self.memory.items()
                     if 0 == prof]
        shuffle(old_words)
        shuffle(new_words)

        day_new_words = new_words[:self.config.day_new]
        day_old_words = old_words[:(self.config.day_cap-len(day_new_words))]
        day_words = day_new_words + day_old_words
        shuffle(day_words)

        self._progress = OrderedDict(
            (word, MemoryStatus.UNKNOWN) for word in day_words
        )

    @property
    def wordlist(self):
        ''' wordlist: {word: text}
        '''
        return self._wordlist

    @property
    def memory(self):
        ''' memory: {word: proficiency}
        proficiency = times of reaching GOOD
        '''
        return self._memory

    @property
    def progress(self):
        ''' progress: {word: status}
        status = {MemoryStatus}
        '''
        return self._progress

    def update_memory(self):
        for word, status in self.progress.items():
            if status == MemoryStatus.GOOD and word not in self._updated:
                self.memory[word] += 1
                self._updated.add(word)

    def i_know(self, word):
        assert self.progress[word] != MemoryStatus.GOOD
        self.progress[word] = self.know_trans[self.progress[word]]

    def i_dont_know(self, word):
        self.progress[word] = MemoryStatus.BAD

    def count_progress(self):
        ''' Count the number of words in each status
        '''
        from collections import Counter
        counter = Counter(v for _, v in self.progress.items())
        return {
            'unknown': counter[MemoryStatus.UNKNOWN],
            'good': counter[MemoryStatus.GOOD],
            'bad': counter[MemoryStatus.BAD],
            'wanting': counter[MemoryStatus.WANTING],
        }

    def next_group(self):
        ''' return: [(word, test), (word, test), ... ]
        '''
        pc = self.count_progress()  # progress counter
        if pc['bad'] == pc['wanting'] == pc['unknown'] == 0:
            return [], pc

        # if there is too many bad words, focus on the bad words
        elif pc['bad'] > self.config.max_bad or \
                pc['wanting'] == pc['unknown'] == 0:
            words = [word for word, status in self.progress.items()
                     if status == MemoryStatus.BAD]
        else:
            words = [word for word, status in self.progress.items()
                     if status in {MemoryStatus.UNKNOWN, MemoryStatus.WANTING}]

        from random import shuffle
        shuffle(words)

        group = []
        for k, word in enumerate(words):
            if k == self.config.group_size:
                break
            group.append({'word': word, 'text': self.wordlist[word]})
        return group, pc
