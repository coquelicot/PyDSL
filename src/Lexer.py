#!/usr/bin/python3

import Parser
import Regex

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
        return "(" + self.name + ":" + ("regex" if self.isRegex else "string") + ":" + self.value + ")"

    def __repr__(self):
        return str(self)

class Lexer:

    def __init__(self, rules, strict=False, ignore=[], charset=frozenset(map(chr, range(128)))):
        self.rules = rules
        self.strict = strict
        self.ignore = ignore
        self.charset = charset

        self.ldfa = None
        for rule in self.rules:
            value = rule.value if rule.isRegex else "\\" + "\\".join(rule.value)
            ldfa = Regex.regexToLDFA(value, self.charset)
            if self.ldfa is None:
                self.ldfa = ldfa
            else:
                self.ldfa.merge(ldfa)
        self.ldfa.minimize()

    def parse(self, string):

        idx = 0
        tokens = []
        while idx < len(string):

            nidx = idx
            cut = None
            self.ldfa.init()

            while nidx < len(string) and not self.ldfa.sinked():
                self.ldfa.shift(string[nidx])
                if self.ldfa.label() > 0:
                    cut = (nidx+1, self.ldfa.label()-1)
                nidx += 1

            if cut:
                if self.rules[cut[1]].name not in self.ignore:
                    tokens.append(Token(self.rules[cut[1]].name, string[idx:cut[0]]))
                idx = cut[0]
            elif not self.strict and string[idx].isspace():
                idx += 1
            else:
                print(string[idx:])
                raise RuntimeError("Can't parse string")
        return tokens

if __name__ == "__main__":
    Lexer([
        Rule("::=", "::=", isRegex=False),
        Rule("%keys", "%keys", isRegex=False),
        Rule("%ignore", "%ignore", isRegex=False),
        Rule("comment", "#[^\n]*\n"),
        Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
        Rule("sqString", "'[^']*'"),
        Rule("dqString", "\"[^\"\\]*(\\\\.[^\"\\]*)*\""),
        Rule("reString", "/[^/\\]*(\\\\.[^/\\]*)*/"),
    ], ignore=["comment"])
