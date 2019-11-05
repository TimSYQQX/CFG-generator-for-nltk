import numpy
from pattern.en import conjugate, lemma, lexeme, PRESENT, PAST, PROGRESSIVE, SINGULAR, PLURAL, PARTICIPLE
from itertools import chain, combinations, permutations
import nltk
import copy


def powerset_reorder(iterable):
    i = list(iterable)
    result = []
    for s in permutations(i):
        for r in range(len(s)+1):
            for t in combinations(s, r):
                result.append([n for n in t])
    return list(numpy.unique(numpy.array(result)))

class Node:
    def __init__(self, value):
        self.value = value
        self.word = []
        self.combination = []
        
    def __str__(self, l=[], t=True):
        if t:
            l=[]
        assert self.word == [] or self.combination == []
#         if self.word==[] and self.combination ==[]:
#             raise ValueError("Tree incomplete")
        if self.word == []:
            buff = ""
            expand = copy.deepcopy(self.combination)
            c = 0
            while c < len(expand):
                i = 0
                while i <len(expand[c]):
                    if type(expand[c][i]) == tuple:
                        ps = powerset_reorder(expand[c][i])
                        base = expand[c]
                        base.pop(i)
                        for elements in ps:
                            tmp = copy.deepcopy(base)
                            tmp = tmp[:i] + elements + tmp[i:]
                            expand.insert(c + 1, tmp)
                        expand.pop(c)
                        c = 0
                        i = 0
                    i += 1
                c += 1
            for comb in expand:
                tmp = ""
                for node in comb:
                    tmp += node.value +" "
                buff += "{} -> {}\n".format(self.value, tmp)
            l.append(self)
            unique = numpy.unique(numpy.array(list(chain.from_iterable(expand))))
            unique.sort()
            for u in unique:
                if not u in l:
                    buff += u.__str__(l, t=False)
                
        elif self.combination == []:
            buff = ""
            word = numpy.unique(numpy.array(self.word.copy()))
            word.sort()
            for c in word:
                buff += "{} -> \"{}\"\n".format(self.value, c)
        target, indices = numpy.unique(numpy.array(buff.split("\n")), return_inverse=True)
        return "\n".join(target[indices])
    
    def get_word(self, l=[], t=True):
        words = []
        if t:
            l=[]
        if self.combination==[]:
            return self.word
        elif self.word==[]:
            unique = numpy.unique(numpy.array(list(chain.from_iterable(self.combination))))
            unique.sort()
            l.append(self)
            for u in unique:
                if u not in l:
                    words.extend(u.get_word(l, t=False))
        return words
            
    def add_word(self, word):
        assert self.combination == []
        if type(word) == str:
            self.word.extend(word.split())
        else:
            self.word.extend(word)
        self.iter = self.word
    
    def add_tense(self):
        assert self.combination == []
        self.add_word(convert(" ".join(self.word), PAST))
        
    def add_comb(self, lst): 
        assert self.word == []
        self.combination.append(lst)
#         self.iter = self.combination
        
    def ext_comb(self, lst):
        assert self.word == []
        assert type(lst[0]) == list
        self.combination.extend(lst)
#         self.iter = self.combination
        
    def get_leaf(self, l=[], root=True):
        if root:
            l = []
        if self.combination == []:
            return [self]
        if self.word == []:
            leaf = []
            l.append(self)
            for node in chain.from_iterable(self.combination):
                if type(node) != tuple and not node in l:
                    leaf.extend(node.get_leaf(l, False))
        return list(numpy.unique(numpy.array(leaf)))
    
    def __ne__(self, obj):
        return self.value != obj.value
    def __eq__(self, obj):
        return self.value == obj.value
    
    def __lt__(self, obj):
        return self.value < obj.value
    
    def __repr__(self):
        return self.value
    
    def __and__(self, node1):
        node0 = self
        word0 = set(node0.word)
        word1 = set(node1.word)
        combination0 = set(node0.combination)
        combination1 = set(node1.combination)
        value0 = node0.value
        value1 = node1.value
        for i0 in range(len(value0)):
            if value0[-i0].isupper():
                break
        for i1 in range(len(value1)):
            if value1[-i1].isupper():
                break
        if value0[-i0] == value1[-i1]:
            value = value0[:-i0]+value1
        else:
            value = value0+"And"+value1
        node = Node(value)
        node.word = list(word0&word1)
        node.combination = list(combination0&combination1)
        return node
    
    def save(self, grammar_dir="Grammar.txt", lexicon_dir="Lexicon.txt"):
        rules = self.__str__().split("\n")
        grammar = []
        lexicon = []
        for r in rules:
            if len(r) > 1:
                if r[-1] == "\"":
                    lexicon.append(r)
                else:
                    grammar.append(r)
        with open(grammar_dir, "w") as f:
            f.write("\n".join(grammar))
        with open(lexicon_dir, "w") as f:
            f.write("\n".join(lexicon))
    
    def get_parser(self):
        grammar = nltk.CFG.fromstring(str(self).split("\n"))
        parser = nltk.ChartParser(grammar)
        return parser

class Verb(Node):
    def __init__(self, value):
        super().__init__(value)
        self.form = {PRESENT:Node("Present" + value), 
                        PAST:Node("Past" + value),
                        PARTICIPLE:Node("Progressive"+value),
                        PAST + PARTICIPLE:Node("PastParticiple"+value),
                        SINGULAR:Node("PresentSingular"+value)
                    }
    
    def add_word(self, word):
        assert self.combination == []
        assert type(word) == str
        for key in self.form.keys():
            buff = ""
            for s in word.split():
                if key==SINGULAR:
                    new = conjugate(verb=s, tense=PRESENT, sp=key)
                elif key == PRESENT:
                    new = lemma(s)
                else:
                    new = conjugate(verb=s, tense=key)
                if new:
                    buff += new + " "
            self.form[key].add_word(buff)
    
    def __getitem__(self, idx):
        return self.form[list(self.form.keys())[idx]]
    
    def __str__(self):
        buff = ""
        unique = self.form.values()
        for c in self.combination:
            tmp = ""
            for i in c:
                tmp += i.value + " "
            buff += "{} -> {}\n".format(self.value, tmp)
        l.append(self)
        for u in unique:
            if not u in l:
                buff += u.__str__([])
         
        
class Word(Node):
    def __init__(self, value, parent=None):
        super().__init__(value)
        self.word = [self.value]
        if parent:
            parent.add_word(self.value)


def generate_random_test(node_lst, num=1000, dir="random_test.txt"):
    node_lst = numpy.array(node_lst)
    node_lst.shuffle()
    buffer = ""
    for i in range(num):
        tmp = ""
        for node in node_lst:
            words = numpy.array(node.get_word())
            words.shuffle()
            word = words[0]
            tmp += word + " "
        tmp += "\n"
        buffer += tmp
    with open(dir, "w") as f:
        f.write(buffer)
        