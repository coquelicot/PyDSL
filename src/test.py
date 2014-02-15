#!/usr/bin/env python3

import Parser, Lexer
from DSL import _lexerParser, _lexerLexer
from DSL import _parserLexer, _parserParser
from DSL import makeParser, makeLexer

lexerLexerConfig = r"""
    %keys ::= '%ignore' '%keys' '::='
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
    sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
    dqString ::= "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""
    comment ::= "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/"
    %ignore ::= comment
"""
lexerLexer = makeLexer(lexerLexerConfig)

lexerParserConfig = r"""
    LexRules ::= rule*
    rule ::= identifier '::=' (sqString | dqString)
           | '%keys' '::=' sqString+
           | '%ignore' '::=' (identifier | sqString)+
    %ignore ::= '::='
"""
lexerParser = makeParser(lexerParserConfig)

parserLexerConfig = r"""
    %keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
    configType ::= "%(ignore|expandSingle|expand)"
    sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
    comment ::= "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/"
    %ignore ::= comment
"""
parserLexer = makeLexer(parserLexerConfig)

parserParserConfig = r"""
    ParseRules ::= rule*
    rule ::= identifier '::=' alternate ('|' alternate)*
           | configType '::=' (identifier | sqString)+
    alternate ::= '$' | rhsItem+
    rhsItem ::= itemValue ('?' | '+' | '*')?
    itemValue ::= identifier | sqString | '(' alternate ('|' alternate)* ')'
    %ignore ::= '::=' '|' '$' '(' ')'
"""
parserParser = makeParser(parserParserConfig)

realOutput = _lexerParser.parse(_lexerLexer.parse(lexerLexerConfig))
testOutput = lexerParser.parse(lexerLexer.parse(lexerLexerConfig))
assert(str(realOutput) == str(testOutput))
realOutput = _lexerParser.parse(_lexerLexer.parse(parserLexerConfig))
testOutput = lexerParser.parse(lexerLexer.parse(parserLexerConfig))
assert(str(realOutput) == str(testOutput))

realOutput = _parserParser.parse(_parserLexer.parse(lexerParserConfig))
testOutput = parserParser.parse(parserLexer.parse(lexerParserConfig))
assert(str(realOutput) == str(testOutput))
realOutput = _parserParser.parse(_parserLexer.parse(parserParserConfig))
testOutput = parserParser.parse(parserLexer.parse(parserParserConfig))
assert(str(realOutput) == str(testOutput))

print('YA!')
