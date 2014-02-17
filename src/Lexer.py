import Parser
import ast

class Token:

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "(" + self.name + ":" + self.value + ")"

    def __repr__(self):
        return str(self)

class Rule:

    def __init__(self, name, value, isRegex=True):
        self.name = name
        self.value = value
        self.isRegex = isRegex

    def __str__(self):
        return "(" + ("regex" if self.isRegex else "string") + ":" + self.value + ")"

    def __repr__(self):
        return str(self)

class Lexer:

    def __init__(self, rules, strict=False, ignore=[]):
        self.rules = rules
        self.strict = strict
        self.ignore = ignore
        self.nfas = []
        for rule in rules:
            self.nfas.append(buildNFA(rule.value, False, not rule.isRegex))

    def parse(self, string):

        tokens = []
        while string != "":

            idx, ntoken = 0, None
            while idx < len(self.rules) and ntoken is None:
                rule = self.rules[idx]
                nfa = self.nfas[idx]
                nfa.init()
                pos, best = 0, 0
                while pos < len(string) and len(nfa.cur) > 0:
                    nfa.trans(string[pos])
                    pos += 1
                    if len(nfa.accepts.intersection(nfa.cur)) > 0:
                        best = pos
                if best > 0:
                    ntoken = Token(rule.name, string[:best])
                idx += 1

            if ntoken:
                if ntoken.name not in self.ignore:
                    tokens.append(ntoken)
                string = string[len(ntoken.value):]
            elif not self.strict and string[0].isspace():
                string = string[1:]
            else:
                print(tokens, string)
                raise RuntimeError("Can't parse string")
        return tokens

class Node:

    def __init__(self, trans=None, etrans=None):
        self.trans = trans if trans else []
        self.etrans = etrans if etrans else set()

    def addTrans(self, func):
        self.trans.append(func)

    def addEtrans(self, node):
        self.etrans.add(node)

    def getTrans(self, ch=None):
        if ch is None:
            return self.etrans
        else:
            result = set()
            for func in self.trans:
                result.update(func(ch))
            return result

class NFA:

    def __init__(self, objSet=None, inverse=False):

        self.cur = None
        if objSet is None:
            self.start = Node()
            self.accepts = set([self.start])

        else:

            self.start = Node()
            accepts = set([Node()])
            self.accepts = accepts

            def tran(ch):
                return accepts if bool(inverse) != (ch in objSet) else set()
            self.start.addTrans(tran)

    def concat(self, obj):
        for accept in self.accepts:
            accept.addEtrans(obj.start)
        self.accepts = obj.accepts

    def union(self, obj):
        nstart, naccept = Node(), Node()
        nstart.addEtrans(self.start)
        nstart.addEtrans(obj.start)
        for accept in self.accepts: accept.addEtrans(naccept)
        for accept in obj.accepts: accept.addEtrans(naccept)
        self.start = nstart
        self.accepts = set([naccept])

    def star(self):
        nstart = Node()
        nstart.addEtrans(self.start)
        for accept in self.accepts: accept.addEtrans(nstart)
        self.start = nstart
        self.accepts = set([nstart])

    def plus(self):
        nstart = Node()
        nstart.addEtrans(self.start)
        for accept in self.accepts: accept.addEtrans(nstart)
        self.accepts = set([nstart])

    def ques(self):
        self.union(NFA())

    def _expand(self):
        idx, que, ncur = 0, list(self.cur), self.cur
        while idx < len(que):
            for node in que[idx].getTrans():
                if node not in ncur:
                    ncur.add(node)
                    que.append(node)
            idx += 1
        self.cur = ncur

    def init(self):
        self.cur = set([self.start])
        self._expand()

    def trans(self, ch):
        ncur = set()
        for node in self.cur:
            ncur.update(node.getTrans(ch))
        self.cur = ncur
        self._expand()

# generate by makeExtparser :)
_parser = Parser.Parser('expr', [Parser.Rule('_extparser_0', ['|', 'concat_expr']), Parser.Rule('_extparser_1', []), Parser.Rule('_extparser_1', ['_extparser_0', '_extparser_1']), Parser.Rule('expr', ['concat_expr', '_extparser_1']), Parser.Rule('_extparser_2', ['decoTerm', '_extparser_2']), Parser.Rule('_extparser_2', ['decoTerm']), Parser.Rule('concat_expr', ['_extparser_2']), Parser.Rule('_extparser_3', []), Parser.Rule('_extparser_3', ['decorator', '_extparser_3']), Parser.Rule('decoTerm', ['term', '_extparser_3']), Parser.Rule('term', ['char']), Parser.Rule('term', ['escaped_char']), Parser.Rule('term', ['(', 'expr', ')']), Parser.Rule('term', ['[', 'expr_set', ']']), Parser.Rule('term', ['.']), Parser.Rule('_extparser_4', []), Parser.Rule('_extparser_4', ['^']), Parser.Rule('_extparser_5', []), Parser.Rule('_extparser_5', ['expr_set_item', '_extparser_5']), Parser.Rule('expr_set', ['_extparser_4', '_extparser_5']), Parser.Rule('expr_set_item', ['expr_set_char']), Parser.Rule('expr_set_item', ['expr_set_range']), Parser.Rule('expr_set_range', ['expr_set_char', '-', 'expr_set_char']), Parser.Rule('escaped_char', ['\\', 'char']), Parser.Rule('escaped_char', ['\\', 'special_char']), Parser.Rule('special_char', ['^']), Parser.Rule('special_char', ['[']), Parser.Rule('special_char', [']']), Parser.Rule('special_char', ['(']), Parser.Rule('special_char', [')']), Parser.Rule('special_char', ['+']), Parser.Rule('special_char', ['*']), Parser.Rule('special_char', ['?']), Parser.Rule('special_char', ['-']), Parser.Rule('special_char', ['$']), Parser.Rule('special_char', ['.']), Parser.Rule('special_char', ['\\']), Parser.Rule('special_char', ['|']), Parser.Rule('expr_set_char', ['char']), Parser.Rule('expr_set_char', ['escaped_char']), Parser.Rule('decorator', ['+']), Parser.Rule('decorator', ['*']), Parser.Rule('decorator', ['?'])], [], ['expr_set_item', 'special_char', 'expr_set_char', 'decorator', '_extparser_0', '_extparser_1', '_extparser_2', '_extparser_3', '_extparser_4', '_extparser_5'], [])

NATIVE_ESCAPE_SET = "abfnrtv"
def getEscapedChar(char):
    if char in NATIVE_ESCAPE_SET:
        return ast.literal_eval('"\\{0}"'.format(char))
    else:
        return char

def buildNFA(string, reverse=False, rawString=False):

    def conv(ch):
        if rawString or ch not in "^[]()+*?-$.\\|":
            return Token('char', ch)
        else:
            return Token(ch, ch)
    tokens = [conv(ch) for ch in string]

    def getChar(node):
        if node.name == 'char':
            return node.value
        else:
            return getEscapedChar(node.child[1].value)

    def toNFA(tree):

        if tree.name == "expr":
            nfa = toNFA(tree.child[0])
            for child in tree.child[2::2]:
                nfa.union(toNFA(child))

        elif tree.name == "concat_expr":
            nfa = NFA()
            for child in (reversed(tree.child) if reverse else tree.child):
                nfa.concat(toNFA(child))

        elif tree.name == 'decoTerm':
            nfa = toNFA(tree.child[0])
            for deco in tree.child[1:]:
                if deco.value == '+':
                    nfa.plus()
                elif deco.value == '*':
                    nfa.star()
                elif deco.value == '?':
                    nfa.ques()

        elif tree.name == 'term':
            child = tree.child[0]
            if child.name == 'char' or child.name == 'escaped_char':
                nfa = NFA(getChar(child))
            elif child.name in '([':
                nfa = toNFA(tree.child[1])
            elif child.name == '.':
                nfa = NFA("", inverse=True)

        elif tree.name == 'expr_set':
            inverse, objSet = False, set()
            for item in tree.child:
                if item.name == '^':
                    inverse = True
                elif item.name == 'expr_set_range':
                    left = getChar(item.child[0])
                    right = getChar(item.child[2])
                    objSet.update(set(map(chr, range(ord(left), ord(right) + 1))))
                else:
                    objSet.add(getChar(item))
            nfa = NFA(objSet, inverse)

        return nfa

    return toNFA(_parser.parse(tokens))

