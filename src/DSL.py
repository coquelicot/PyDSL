import Lexer
import Parser

_lexerLexer = Lexer.Lexer([
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("%keys", "%keys", isRegex=False),
    Lexer.Rule("%ignore", "%ignore", isRegex=False),
    Lexer.Rule("comment", "#[^\n]*\n"),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^']*'"),
    Lexer.Rule("dqString", "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""),
    Lexer.Rule("reString", "/[^/\\\\]*(\\\\.[^/\\\\]*)*/"),
], ignore=["comment"])
_lexerParser = Parser.Parser("LexRules", [
    Parser.Rule("LexRules", ["rules"]),
    Parser.Rule("rules", []),
    Parser.Rule("rules", ["rule", "rules"]),
    Parser.Rule("rule", ["identifier", "::=", "sqString"]),
    Parser.Rule("rule", ["identifier", "::=", "dqString"]),
    Parser.Rule("rule", ["identifier", "::=", "reString"]),
    Parser.Rule("rule", ["%keys", "::=", "keys"]),
    Parser.Rule("rule", ["%ignore", "::=", "elements"]),
    Parser.Rule("keys", ["key"]),
    Parser.Rule("keys", ["key", "keys"]),
    Parser.Rule("key", ["sqString"]),
    Parser.Rule("key", ["dqString"]),
    Parser.Rule("elements", ["element"]),
    Parser.Rule("elements", ["element", "elements"]),
    Parser.Rule("element", ["identifier"]),
    Parser.Rule("element", ["sqString"]),
], expand=["rules", "keys", "key", "element", "elements"], ignore=["::="])

_parserLexer = Lexer.Lexer([
    Lexer.Rule("$", "$", isRegex=False),
    Lexer.Rule("|", "|", isRegex=False),
    Lexer.Rule("(", "(", isRegex=False),
    Lexer.Rule(")", ")", isRegex=False),
    Lexer.Rule("$", "$", isRegex=False),
    Lexer.Rule("+", "+", isRegex=False),
    Lexer.Rule("*", "*", isRegex=False),
    Lexer.Rule("?", "?", isRegex=False),
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("configType", "%(ignore|expandSingle|expand)"),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^']*'"),
    Lexer.Rule("dqString", "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""),
    Lexer.Rule("comment", "#[^\n]*\n"),
], ignore=["comment"])
_parserParser = Parser.Parser('ParseRules', [
    Parser.Rule('ParseRules', ['rules']),
    Parser.Rule('rules', []),
    Parser.Rule('rules', ['rule', 'rules']),
    Parser.Rule('rule', ['identifier', '::=', 'alternates']),
    Parser.Rule('rule', ['configType', '::=', 'simpleItems']),
    Parser.Rule('alternates', ['alternate']),
    Parser.Rule('alternates', ['alternate', '|', 'alternates']),
    Parser.Rule('alternate', ['$']),
    Parser.Rule('alternate', ['rhsItems']),
    Parser.Rule('rhsItems', ['rhsItem']),
    Parser.Rule('rhsItems', ['rhsItem', 'rhsItems']),
    Parser.Rule('rhsItem', ['itemValue', 'decorator']),
    Parser.Rule('itemValue', ['simpleItem']),
    Parser.Rule('itemValue', ['(', 'alternates', ')']),
    Parser.Rule('decorator', []),
    Parser.Rule('decorator', ['?']),
    Parser.Rule('decorator', ['+']),
    Parser.Rule('decorator', ['*']),
    Parser.Rule('simpleItems', ['simpleItem']),
    Parser.Rule('simpleItems', ['simpleItem', 'simpleItems']),
    Parser.Rule('simpleItem', ['identifier']),
    Parser.Rule('simpleItem', ['dqString']),
    Parser.Rule('simpleItem', ['sqString'])
], expand=['rules', 'rhsItems', 'alternates', 'decorator', 'simpleItem', 'simpleItems'], ignore=['::=', '|', '$', '(', ')'])

def escape(string):
    ret, inEscape = "", False
    for ch in string[1:-1]:
        if inEscape:
            ret += Lexer.getEscapedChar(ch)
            inEscape = False
        elif ch != "\\":
            ret += ch
        else:
            inEscape = True
    return ret

def makeLexer(config):

    tokens = _lexerLexer.parse(config)
    lexerRules = _lexerParser.parse(tokens)

    keys = []
    regexs = []
    ignore = []
    for rule in lexerRules.child:
        if rule.child[0].name == '%keys':
            for token in rule.child[1:]:
                key = escape(token.value)
                keys.append(Lexer.Rule(key, key, isRegex=False))
        elif rule.child[0].name == '%ignore':
            for token in rule.child[1:]:
                if token.name == 'identifier':
                    ignore.append(token.value)
                else:
                    ignore.append(escape(token.value))
        else:
            name = rule.child[0].value
            if rule.child[1].name == 'dqString':
                value = escape(rule.child[1].value)
            elif rule.child[1].name in ['sqString', 'reString']:
                value = rule.child[1].value[1:-1]
            isRegex = rule.child[1].name == 'reString'
            regexs.append(Lexer.Rule(name, value, isRegex=isRegex))
    return Lexer.Lexer(keys + regexs, ignore=ignore)

def makeParser(config, start=None):
    tokens = _parserLexer.parse(config)
    tree = _parserParser.parse(tokens)
    return _makeParser(tree, start)

def _makeParser(tree, start=None):

    expand = []
    rules = []
    extraConfig = {}
    prefix = "_parser_"

    def allocName():
        expand.append(prefix + str(len(expand)))
        return expand[-1]

    def getRule(node, _lhs=None):
        rhs = []
        lhs = _lhs if _lhs else allocName()

        for _node in node.child:

            itemValue = _node.child[0]
            firstChild = itemValue.child[0]

            if firstChild.name == 'alternate':
                itemName = getRules(itemValue.child)
            elif firstChild.name == 'identifier':
                itemName = firstChild.value
            elif firstChild.name == 'dqString':
                itemName = escape(firstChild.value)
            elif firstChild.name == 'sqString':
                itemName = firstChild.value[1:-1]

            if len(_node.child) > 1:
                decorator = _node.child[1].value
                _itemName = allocName()
                if decorator in "?*":
                    rules.append(Parser.Rule(_itemName, []))
                if decorator in "*+":
                    rules.append(Parser.Rule(_itemName, [itemName, _itemName]))
                if decorator in "+?":
                    rules.append(Parser.Rule(_itemName, [itemName]))
                rhs.append(_itemName)
            else:
                rhs.append(itemName)

        rules.append(Parser.Rule(lhs, rhs))
        return lhs

    def getRules(nodes, _lhs=None):
        lhs = _lhs if _lhs else allocName()
        for node in nodes:
            getRule(node, lhs)
        return lhs

    for rule in tree.child:
        if rule.child[0].name == 'configType':
            objList = extraConfig.setdefault(rule.child[0].value[1:], [])
            for _node in rule.child[1:]:
                objList.append(_node.value if _node.name == 'identifier' else escape(_node.value))
        else:
            lhs = rule.child[0].value
            if start is None:
                start = lhs
            getRules(rule.child[1:], lhs)
    extraConfig.setdefault('expand', []).extend(expand)

    return Parser.Parser(start, rules, **extraConfig)

class DSL:

    def __init__(self, lexer, parser):
        self.lexer = lexer
        self.parser = parser

    def parse(self, config):
        return self.parser.parse(self.lexer.parse(config))

_dslLexer = makeLexer(r"""#dsl
    %keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
    identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
    sqString ::= /'[^']*'/
    dqString ::= /"[^"\\]*(\\.[^"\\]*)*"/
    reString ::= /\/[^\/\\]*(\\.[^\/\\]*)*\//
    configType ::= /%(ignore|expandSingle|expand)/
    comment ::= /#[^\n]*\n/
    %ignore ::= comment
""")
_dslParser = makeParser(r"""#dsl
    DSLRules ::= rule*
    rule ::= identifier '::=' reString # define RE
           | identifier '::=' alternate ('|' alternate)*
           | configType '::=' simpleItem+
    alternate ::= '$' | rhsItem+
    rhsItem ::= itemValue ('?' | '+' | '*')?
    itemValue ::= simpleItem | '(' alternate ('|' alternate)* ')'
    simpleItem ::= identifier | dqString | sqString
    %ignore ::= '::=' '|' '$' '(' ')'
    %expand ::= simpleItem
""")

def makeDSL(config):

    tokens = _dslLexer.parse(config)
    tree = _dslParser.parse(tokens)

    keySet = set()
    def getKeys(ast):
        if isinstance(ast, Lexer.Token):
            if ast.name == 'sqString':
                keySet.add(ast.value[1:-1])
            elif ast.name == 'dqString':
                keySet.add(escape(ast.value))
        else:
            for child in ast.child:
                getKeys(child)
    getKeys(tree)
    keys = [Lexer.Rule(key, key, isRegex=False) for key in keySet]

    nchild = []
    regexs = []
    for rule in tree.child:
        if rule.child[1].name == 'reString':
            regexs.append(Lexer.Rule(rule.child[0].value, rule.child[1].value[1:-1], isRegex=True))
        else:
            nchild.append(rule)
    tree.child = nchild

    lexer = Lexer.Lexer(list(keys) + regexs)
    parser = _makeParser(tree)
    return DSL(lexer, parser)
