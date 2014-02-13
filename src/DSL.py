import Lexer
import Parser

_lexerLexer = Lexer.Lexer([
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("%keys", "%keys", isRegex=False),
    Lexer.Rule("%ignore", "%ignore", isRegex=False),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"),
    Lexer.Rule("dqString", "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""),
    Lexer.Rule("comment", "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/")
], ignore=["comment"])
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
    Lexer.Rule("(", "(", isRegex=False),
    Lexer.Rule(")", ")", isRegex=False),
    Lexer.Rule("$", "$", isRegex=False),
    Lexer.Rule("+", "+", isRegex=False),
    Lexer.Rule("*", "*", isRegex=False),
    Lexer.Rule("?", "?", isRegex=False),
    Lexer.Rule("::=", "::=", isRegex=False),
    Lexer.Rule("configType", "%(ignore|expandSingle|expand)"),
    Lexer.Rule("identifier", "[_a-zA-Z][_a-zA-Z0-9]*"),
    Lexer.Rule("sqString", "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"),
    Lexer.Rule("comment", "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/")
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
    Parser.Rule('itemValue', ['identifier']),
    Parser.Rule('itemValue', ['sqString']),
    Parser.Rule('itemValue', ['(', 'alternates', ')']),
    Parser.Rule('decorator', []),
    Parser.Rule('decorator', ['?']),
    Parser.Rule('decorator', ['+']),
    Parser.Rule('decorator', ['*']),
    Parser.Rule('simpleItems', ['simpleItem']),
    Parser.Rule('simpleItems', ['simpleItem', 'simpleItems']),
    Parser.Rule('simpleItem', ['identifier']),
    Parser.Rule('simpleItem', ['sqString'])
], expand=['rules', 'rhsItems', 'alternates', 'decorator', 'simpleItem', 'simpleItems'], ignore=['::=', '|', '$', '(', ')'])

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

    expand = []
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
    tokens = _parserLexer.parse(config)
    tree = _parserParser.parse(tokens)

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

