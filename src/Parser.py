
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
        return State(self.rule, self.pos + 1, self.orgi, self.node.extended(nch))

    def __str__(self):
        return "(" + str(self.rule) + ":" + str(self.pos) + ":" + str(self.orgi) + ")"
    
    def __eq__(self, obj):
        return self.rule == obj.rule and self.orgi == obj.orgi and self.pos == obj.pos

    def __hash__(self):
        return hash((self.rule, self.pos, self.orgi))

class Parser:

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
        self.initState = State(self.initRule)
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
                        self.add(State(rule, 0, pos), pos)

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
