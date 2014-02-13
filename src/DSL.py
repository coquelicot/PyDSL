import Lexer
import Parser

_lexerLexer = Lexer.Lexer([
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("%keys", "%keys", isRegex=False),
    Lexer.Rule("%ignore", "%ignore", isRegex=False),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"),
    Lexer.Rule("dqString", "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""),
])
_lexerParser = Parser.Parser("LexRules", [
    Parser.Rule("LexRules", ["rules"]),
    Parser.Rule("rules", []),
    Parser.Rule("rules", ["rule", "rules"]),
    Parser.Rule("rule", ["identifier", "::=", "sqString"]),
    Parser.Rule("rule", ["identifier", "::=", "dqString"]),
    Parser.Rule("rule", ["%keys", "::=", "keys"]),
    Parser.Rule("rule", ["%ignore", "::=", "identifiers"]),
    Parser.Rule("keys", ["sqString"]),
    Parser.Rule("keys", ["sqString", "keys"]),
    Parser.Rule("identifiers", ["identifier"]),
    Parser.Rule("identifiers", ["identifier", "identifiers"]),
], expand=["rules", "keys", "identifiers"], ignore=["::="])

_parserLexer = Lexer.Lexer([
    Lexer.Rule("$", "$", isRegex=False),
    Lexer.Rule("|", "|", isRegex=False),
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("configType", "%(ignore|expandSingle|expand)"),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"),
])
_parserParser = Parser.Parser("ParseRules", [
    Parser.Rule("ParseRules", ["rules"]),
    Parser.Rule("rules", []),
    Parser.Rule("rules", ["rule", "rules"]),
    Parser.Rule("rule", ["identifier", "::=", "alternates"]),
    Parser.Rule("rule", ["configType", "::=", "rhsItems"]),
    Parser.Rule("alternates", ["alternate"]),
    Parser.Rule("alternates", ["alternate", "|", "alternates"]),
    Parser.Rule("alternate", ["$"]),
    Parser.Rule("alternate", ["rhsItems"]),
    Parser.Rule("rhsItems", ["rhsItem"]),
    Parser.Rule("rhsItems", ["rhsItem", "rhsItems"]),
    Parser.Rule("rhsItem", ["identifier"]),
    Parser.Rule("rhsItem", ["sqString"]),
], expand=["rules", "rhsItems", "rhsItem", "alternates"], ignore=["::=", "|", "$"])

def escape(string):
    ret, inEscape = "", False
    for ch in string[1:-1]:
        if inEscape or ch != "\\":
            ret += ch
            inEscape = False
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
                ignore.append(token.value)
        else:
            name = rule.child[0].value
            value = escape(rule.child[1].value)
            isRegex = rule.child[1].name == 'dqString'
            regexs.append(Lexer.Rule(name, value, isRegex=isRegex))
    return Lexer.Lexer(keys + regexs, ignore=ignore)

def makeParser(config, start=None):

    tokens = _parserLexer.parse(config)
    parserRules = _parserParser.parse(tokens)

    def _escape(node):
        if node.name == 'identifier':
            return node.value
        else:
            return escape(node.value)

    rules = []
    extraConfig = {}
    for rule in parserRules.child:
        if rule.child[0].name == 'configType':
            configType = rule.child[0].value[1:]
            configValue = list(map(_escape, rule.child[1:]))
            extraConfig[configType] = configValue
        else:
            lhs = rule.child[0].value
            for alternate in rule.child[1:]:
                rhs = list(map(_escape, alternate.child))
                nrule = Parser.Rule(lhs, rhs)
                rules.append(nrule)

    if start is None and len(rules) > 0:
        start = rules[0].lhs
    return Parser.Parser(start, rules, **extraConfig)

_extparserLexer = makeLexer(r"""
    %keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
    configType ::= "%(ignore|expandSingle|expand)"
    sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
    comment ::= "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/"
    %ignore ::= comment
""")
_extparserParser = makeParser(r"""
    ExtParseRules ::= rules
    rules ::= rule rules | $
    rule ::= identifier '::=' alternates | configType '::=' simpleItems
    alternates ::= alternate | alternate '|' alternates
    alternate ::= '$' | rhsItems
    rhsItems ::= rhsItem | rhsItem rhsItems
    rhsItem ::= itemValue decorator
    itemValue ::= identifier | sqString | '(' alternates ')'
    decorator ::= '?' | '+' | '*' | $
    simpleItems ::= simpleItem | simpleItem simpleItems
    simpleItem ::= identifier | sqString
    %expand ::= rules rhsItems alternates decorator simpleItem simpleItems
    %ignore ::= '::=' '|' '$' '(' ')'
""")

def makeExtparser(config, start=None):

    expand = []
    prefix = "_extparser_"
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
            elif firstChild.name == 'sqString':
                itemName = escape(firstChild.value)

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

    rules = []
    extraConfig = {}
    tokens = _extparserLexer.parse(config)
    tree = _extparserParser.parse(tokens)

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

