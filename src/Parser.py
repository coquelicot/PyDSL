
class Rule:

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return "({0} => {1})".format(self.lhs, self.rhs)

    def __repr__(self):
        return "{0}({1}, {2})".format(self.__class__.__qualname__, repr(self.lhs), repr(self.rhs))

    def __eq__(self, obj):
        return self.lhs == obj.lhs and self.rhs == obj.rhs

    def __hash__(self):
        return hash((self.lhs, '\\'.join(self.rhs)))

class Node:
    
    def __init__(self, name, child):
        self.name = name
        self.child = child

    def extended(self, nch):
        return Node(self.name, self.child + [nch])

    def __str__(self, depth=0):
        result = '  ' * depth + self.name + "\n"
        depth += 1
        for ch in self.child:
            if isinstance(ch, Node):
                result += ch.__str__(depth)
            else:
                result += '  ' * depth + str(ch) + "\n"
        return result

    def __repr__(self):
        return str(self)

class Parser:

    class State:

        def __init__(self, rule, pos=0, orgi=0, node=None):
            self.rule = rule
            self.pos = pos
            self.orgi = orgi
            self.node = Node(rule.lhs, []) if node is None else node

        def nextRHS(self):
            return None if self.isComplete() else self.rule.rhs[self.pos]

        def isComplete(self):
            return self.pos == len(self.rule.rhs)

        def advanced(self, nch):
            return Parser.State(self.rule, self.pos + 1, self.orgi, self.node.extended(nch))

        def __str__(self):
            return "(" + str(self.rule) + ":" + str(self.pos) + ":" + str(self.orgi) + ")"

        def __eq__(self, obj):
            return self.rule == obj.rule and self.orgi == obj.orgi and self.pos == obj.pos

        def __hash__(self):
            return hash((self.rule, self.pos, self.orgi))


    INIT_SYM = "$"

    def __init__(self, start, rules, ignore=[], expand=[], expandSingle=[]):

        self.start = start
        self.ignore = ignore
        self.expand = expand
        self.expandSingle = expandSingle
        self.orgiRules = rules

        self.chart = None
        self.mchart = None
        self.initRule = Rule(Parser.INIT_SYM, [start])
        self.initState = self.State(self.initRule)
        self.rules = {}
        for rule in self.orgiRules:
            if rule.lhs not in self.rules:
                self.rules[rule.lhs] = []
            self.rules[rule.lhs].append(rule)

    def __repr__(self):
        return "{0}({1}, {2}, {3}, {4}, {5})".format(
            self.__class__.__qualname__,
            repr(self.start),
            repr(self.orgiRules),
            repr(self.ignore),
            repr(self.expand),
            repr(self.expandSingle))

    def parse(self, tokens):

        self.chart = [[self.initState]]
        self.mchart = [{self.initRule.rhs[0]: set([self.initState])}]
        for pos in range(len(tokens) + 1):
            self.chart.append([])
            self.mchart.append({})

            _idx = 0
            while _idx < len(self.chart[pos]):
                state = self.chart[pos][_idx]
                _idx += 1

                if state.isComplete():
                    for _state in self.mchart[state.orgi].setdefault(state.rule.lhs, set()):
                        self.add(_state.advanced(state.node), pos)

                elif state.nextRHS() in self.rules:
                    for rule in self.rules[state.nextRHS()]:
                        self.add(self.State(rule, 0, pos), pos)

                elif pos < len(tokens) and state.nextRHS() == tokens[pos].name:
                    self.add(state.advanced(tokens[pos]), pos + 1)

        for state in self.chart[len(tokens)]:
            if state.isComplete() and state.rule.lhs == Parser.INIT_SYM:
                result = self.flatten(state.node.child[0])
                if len(result) != 1:
                    raise RuntimeError("The simplified AST is not a tree.")
                else:
                    return result[0]
        raise RuntimeError("Can't parse token stream.")

    def add(self, state, pos):
        if state not in self.mchart[pos].setdefault(state.nextRHS(), set()):
            self.chart[pos].append(state)
            self.mchart[pos][state.nextRHS()].add(state)

    def flatten(self, node):
        if node.name in self.ignore:
            return []

        nchild = []
        for ch in node.child:
            if isinstance(ch, Node):
                nchild.extend(self.flatten(ch))
            elif ch.name not in self.ignore:
                nchild.append(ch)
        if node.name in self.expand or (node.name in self.expandSingle and len(nchild) == 1):
            return nchild
        else:
            node.child = nchild
            return [node]

class LR1Parser:

    class Item:

        def __init__(self, rule, pos=0, follow=None):
            self.rule = rule
            self.pos = pos
            self.follow = follow

        def isComplete(self):
            return self.pos == len(self.rule.rhs)

        def nextRHS(self):
            return None if self.isComplete() else self.rule.rhs[self.pos]

        def advanced(self):
            return LR1Parser.Item(self.rule, self.pos + 1, self.follow)

        def __hash__(self):
            return hash((self.rule, self.pos, self.follow))

        def __eq__(self, obj):
            return self.rule == obj.rule and self.pos == obj.pos and self.follow == obj.follow

        def __str__(self):
            return "(" + str(self.rule) + ":" + str(self.pos) + ":" + str(self.follow) + ")"

        def __repr__(self):
            return str(self)


    INIT_SYM = "$"

    def __init__(self, start, rules, ignore=[], expand=[], expandSingle=[]):

        self.start = start
        self.ignore = ignore
        self.expand = expand
        self.expandSingle = expandSingle
        self.orgiRules = rules

        self.initRule = Rule(LR1Parser.INIT_SYM, [start])
        self.initItem = self.Item(self.initRule)
        self.rules = {}
        for rule in self.orgiRules:
            if rule.lhs not in self.rules:
                self.rules[rule.lhs] = []
            self.rules[rule.lhs].append(rule)

        self.build_first()
        self.build()

    def build_first(self):
        update = True
        firsts = dict([(lhs, set()) for lhs in self.rules.keys()])
        while update:
            update = False
            for lhs, rules in self.rules.items():
                objSet = firsts[lhs]
                for rule in rules:
                    first_rhs = rule.rhs[0] if len(rule.rhs) > 0 else None
                    if first_rhs in self.rules:
                        if not firsts[first_rhs].issubset(objSet):
                            update = True
                            objSet.update(firsts[first_rhs])
                    else:
                        if first_rhs not in objSet:
                            objSet.add(first_rhs)
        self.firsts = firsts

    def first_of(self, rhs):
        ret = set([None])
        for tok in rhs:
            if None not in ret:
                break
            ret.remove(None)
            if tok in self.firsts:
                ret.update(self.firsts[tok])
            else:
                ret.add(tok)
        return ret

    def closure(self, itemSet):
        que = list(itemSet)
        while len(que) > 0:
            _que, que = que, []
            for item in _que:
                if not item.isComplete() and item.nextRHS() in self.rules:
                    follows = self.first_of(item.rule.rhs[item.pos+1:] + [item.follow])
                    for rule in self.rules[item.nextRHS()]:
                        for follow in follows:
                            newItem = self.Item(rule, follow=follow)
                            if newItem not in itemSet:
                                itemSet.add(newItem)
                                que.append(newItem)
        return itemSet

    def build(self):

        idx = 0
        edges = []
        reduces = []
        CCs = [self.closure(set([self.initItem]))]

        while idx < len(CCs):

            itemsMap = {}
            reduceMap = {}
            for item in CCs[idx]:
                if not item.isComplete():
                    rhs = item.nextRHS()
                    if rhs not in itemsMap:
                        itemsMap[rhs] = set()
                    itemsMap[rhs].add(item.advanced())
                else:
                    if item.follow in reduceMap:
                        raise RuntimeError("Not LR1")
                    else:
                        reduceMap[item.follow] = item.rule
            for itemSet in itemsMap.values():
                self.closure(itemSet)

            for itemSet in itemsMap.values():
                if itemSet not in CCs:
                    CCs.append(itemSet)

            edges.append(dict())
            for lhs, itemSet in itemsMap.items():
                edges[-1][lhs] = CCs.index(itemSet)
            reduces.append(reduceMap)

            if not set(reduceMap.keys()).isdisjoint(set(itemsMap.keys())):
                raise RuntimeError("Not LR1")

            idx += 1

        self.edges = edges
        self.reduces = reduces

    def parse(self, tokens):

        stack = [0]

        def reduceBy(lhs):
            rule = self.reduces[stack[-1]][lhs]
            chds = []
            for i in range(len(rule.rhs)):
                stack.pop()
                chds.append(stack.pop())
            assert rule.lhs in self.edges[stack[-1]]
            obj = self.edges[stack[-1]][rule.lhs]
            stack.append(Node(rule.lhs, reversed(chds)))
            stack.append(obj)

        for tok in tokens:
            while tok.name in self.reduces[stack[-1]]:
                reduceBy(tok.name)
            if tok.name in self.edges[stack[-1]]:
                obj = self.edges[stack[-1]][tok.name]
                stack.append(tok)
                stack.append(obj)
            else:
                raise RuntimeError("Can't parse token stream.")

        while None in self.reduces[stack[-1]]:
            if self.reduces[stack[-1]][None] == self.initRule:
                result = self.flatten(stack[-2])
                if len(result) != 1:
                    raise RuntimeError("The simplified AST is not a tree.")
                else:
                    return result[0]
            else:
                reduceBy(None)
        raise RuntimeError("Can't parse token stream.")

    def flatten(self, node):
        if node.name in self.ignore:
            return []

        nchild = []
        for ch in node.child:
            if isinstance(ch, Node):
                nchild.extend(self.flatten(ch))
            elif ch.name not in self.ignore:
                nchild.append(ch)
        if node.name in self.expand or (node.name in self.expandSingle and len(nchild) == 1):
            return nchild
        else:
            node.child = nchild
            return [node]
