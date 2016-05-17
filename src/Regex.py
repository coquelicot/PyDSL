#!/usr/bin/python3

class SimpleNFA:

    class Node:

        def __init__(self, tran=lambda x: None, link=None):
            self.tran = tran
            self.link = link if link else set()

    def __init__(self, accepts=set(), reverse=False):
        accept = self.Node()
        self.accept = accept
        self.start = self.Node(lambda x: accept if reverse ^ (x in accepts) else None)

    def star(self):
        nstart = self.Node(link=set([self.start]))
        self.accept.link.add(nstart)
        self.start = nstart
        self.accept = nstart
        return self

    def plus(self):
        naccept = self.Node(link=set([self.start]))
        self.accept.link.add(naccept)
        self.accept = naccept
        return self

    def maybe(self):
        naccept = self.Node()
        self.accept.link.add(naccept)
        self.start.link.add(naccept)
        self.accept = naccept
        return self

    def concat(self, obj):
        self.accept.link.add(obj.start)
        self.accept = obj.accept
        return self

    def union(self, obj):
        nstart = self.Node(link=set([self.start, obj.start]))
        naccept = self.Node()
        self.accept.link.add(naccept)
        obj.accept.link.add(naccept)
        self.start = nstart
        self.accept = naccept
        return self

    def startState(self):
        return self.expand([self.start])

    @classmethod
    def expand(cls, nodes):
        ret = set(nodes)
        que = list(ret)
        while len(que) > 0:
            cur = que.pop()
            for adj in cur.link:
                if adj not in ret:
                    ret.add(adj)
                    que.append(adj)
        return frozenset(ret)

    @classmethod
    def move(cls, nodes, ch):
        return cls.expand(filter(lambda x: x is not None, map(lambda nd: nd.tran(ch), nodes)))

    def init(self):
        self.cur = self.startState()

    def shift(self, ch):
        self.cur = self.move(self.cur, ch)

    def isAccept(self):
        return self.accept in self.cur

    def willAccept(self, obj):
        return self.accept in obj

    @classmethod
    def fromRegex(cls, config):

        idx = 0
        stk = []

        def shift():
            tmp = []
            while len(stk) > 0 and stk[-1] != "(" and stk[-1] != "|":
                tmp.append(stk.pop())
            nfa = tmp.pop()
            while len(tmp) > 0:
                nfa.concat(tmp.pop())
            if len(stk) > 0 and stk[-1] == "|":
                stk.pop()
                nfa.union(stk.pop())
            return nfa

        while idx < len(config):

            if config[idx] == "\\":
                stk.append(SimpleNFA(config[idx+1]))
                idx += 2

            elif config[idx] == "*":
                stk[-1].star()
                idx += 1
            elif config[idx] == "+":
                stk[-1].plus()
                idx += 1
            elif config[idx] == "?":
                stk[-1].maybe()
                idx += 1

            elif config[idx] == ".":
                stk.append(SimpleNFA(set(), True))
                idx += 1

            elif config[idx] == "(":
                stk.append("(")
                idx += 1

            elif config[idx] == "|":
                nfa = shift()
                stk.append(nfa)
                stk.append("|")
                idx += 1

            elif config[idx] == ")":
                nfa = shift()
                if len(stk) > 0:
                    stk[-1] = nfa
                else:
                    stk.append(nfa)
                idx += 1

            elif config[idx] == "[":

                if config[idx+1] == "^":
                    nega = True
                    idx += 2
                else:
                    nega = False
                    idx += 1

                chars = []
                while config[idx] != "]":
                    if config[idx] == "-" and config[idx+1] != "]" and len(chars) > 0:
                        for code in range(ord(chars[-1])+1, ord(config[idx+1])+1):
                            chars.append(chr(code))
                        idx += 2
                    else:
                        chars.append(config[idx])
                        idx += 1
                idx += 1

                stk.append(SimpleNFA(set(chars), nega))
            
            else:
                stk.append(SimpleNFA(config[idx]))
                idx += 1

        nfa = shift()
        assert len(stk) == 0
        return nfa

class DFA:

    def __init__(self, edges, accepts):
        self.edges = edges
        self.accepts = accepts
        self.charset = set(edges[0].keys())
        for es in edges[1:]:
            assert self.charset == set(es.keys())

    def __repr__(self):
        return "{e:" + str(self.edges) + ", ac:" + str(self.accepts) + "}"

    def init(self):
        self.cur = 0
    def shift(self, ch):
        self.cur = self.edges[self.cur][ch]
    def isAccept(self):
        return self.cur in self.accepts

    @classmethod
    def fromNFA(cls, nfa, charset):

        idx = 0
        que = [nfa.startState()]
        indexMap = {que[0]:0}
        edges = []
        accepts = []

        while idx < len(que):
            cur = que[idx]
            if nfa.willAccept(cur):
                accepts.append(idx)
            edges.append(dict())
            for ch in charset:
                adj = SimpleNFA.move(cur, ch)
                if adj not in indexMap:
                    indexMap[adj] = len(indexMap)
                    que.append(adj)
                edges[-1][ch] = indexMap[adj]
            idx += 1

        return DFA(edges, accepts)

class LDFA:

    def __init__(self, dfas, edges, labels, charset):
        self.dfas = dfas
        self.edges = edges
        self.labels = labels
        self.charset = charset

    def __repr__(self):
        return "{e:" + str(self.edges) + ", lb:" + str(self.labels) + "}"

    def init(self):
        self.cur = 0
    def shift(self, ch):
        self.cur = self.edges[self.cur][ch]
    def label(self):
        return self.labels[self.cur]
    def sinked(self):
        return self.cur == self.sink

    def merge(self, obj):

        idx = 0
        que = [(0, 0)]
        indexMap = {que[0]:0}
        nedges = []
        nlabels = []
        assert self.charset == obj.charset

        while idx < len(que):
            cur = que[idx]
            idx += 1
            nedges.append({})
            for ch in self.charset:
                nex = (self.edges[cur[0]][ch], obj.edges[cur[1]][ch])
                if nex not in indexMap:
                    indexMap[nex] = len(indexMap)
                    que.append(nex)
                nedges[-1][ch] = indexMap[nex]
            nlabels.append(self.labels[cur[0]] if obj.labels[cur[1]] == 0 else obj.labels[cur[1]] + len(self.dfas))

        self.dfas += obj.dfas
        self.edges = nedges
        self.labels = nlabels

    def minimize(self):

        group = self.labels[:]
        def getIdent(idx):
            return (group[idx], tuple(map(lambda ch: group[self.edges[idx][ch]], self.charset)))

        while True:
            ngroup = []
            indexMap = {}
            for ident in map(getIdent, range(len(self.edges))):
                if ident not in indexMap:
                    indexMap[ident] = len(indexMap)
                ngroup.append(indexMap[ident])
            if ngroup == group:
                break
            else:
                group = ngroup

        groups = [[] for x in range(max(group)+1)]
        for i in range(len(group)):
            groups[group[i]].append(i)

        nedges = list(map(lambda grp: dict(map(lambda ch: (ch, group[self.edges[grp[0]][ch]]), self.charset)), groups))
        nlabels = list(map(lambda grp: self.labels[grp[0]], groups))

        self.edges = nedges
        self.labels = nlabels
        for idx in range(len(self.edges)):
            if self.labels[idx] == 0 and all(map(lambda x: x == idx, self.edges[idx].values())):
                self.sink = idx

    @classmethod
    def fromDFA(cls, dfa):
        dfas = [dfa]
        edges = dfa.edges
        labels = list(map(lambda x: 1 if x in dfa.accepts else 0, range(len(dfa.edges))))
        charset = dfa.charset
        return LDFA(dfas, edges, labels, charset)

def regexToLDFA(regex, charset):
    return LDFA.fromDFA(DFA.fromNFA(SimpleNFA.fromRegex(regex), charset))

if __name__ == "__main__":
    
    # a+b
    r1 = "a+b?b?b?b?b?b*"
    r2 = "a?a?a?a?a?a*b+"
    r3 = "ab|b+a*"
    chars = "ab"
    nfa1 = SimpleNFA.fromRegex(r1)
    nfa2 = SimpleNFA.fromRegex(r2)
    nfa3 = SimpleNFA.fromRegex(r3)
    dfa1 = DFA.fromNFA(nfa1, chars)
    dfa2 = DFA.fromNFA(nfa2, chars)
    dfa3 = DFA.fromNFA(nfa3, chars)

    ldfa1 = LDFA.fromDFA(dfa1)
    ldfa2 = LDFA.fromDFA(dfa2)
    ldfa3 = LDFA.fromDFA(dfa3)
    ldfa2.merge(ldfa3)
    ldfa1.merge(ldfa2)
    ldfa1.minimize()

    print(ldfa1)

    while True:
        s = input().strip()
        ldfa1.init()
        for ch in s:
            ldfa1.shift(ch)
        print(ldfa1.label())
        print(ldfa1.sinked())
