#!/usr/bin/env python3

import Parser, Lexer
from DSL import _lexerParser, _lexerLexer
from DSL import _parserLexer, _parserParser
from DSL import _extparserLexer, _extparserParser
from DSL import makeParser, makeLexer, makeExtparser

lexerLexerConfig = r"""
    %keys ::= '%keys' '::='
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
    sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
    dqString ::= "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""
"""
lexerLexer = makeLexer(lexerLexerConfig)

lexerParserConfig = r"""
    LexRules ::= rules
    rules ::= rule rules | $
    rule ::= identifier '::=' sqString
           | identifier '::=' dqString
           | '%keys' '::=' keys
    keys ::= sqString keys | $

    %ignore ::= '::='
    %expand ::= rules keys
"""
lexerParser = makeParser(lexerParserConfig)

parserLexerConfig = r"""
    %keys ::= '$' '|' '::='
    configType ::= "%(ignore|expandSingle|expand)"
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
    sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
"""
parserLexer = makeLexer(parserLexerConfig)

parserParserConfig = r"""
    ParseRules ::= rules
    rules ::= rule rules | $
    rule ::= identifier '::=' alternates | configType '::=' rhsItems
    alternates ::= alternate | alternate '|' alternates
    alternate ::= '$' | rhsItems
    rhsItems ::= rhsItem | rhsItem rhsItems
    rhsItem ::= identifier | sqString
    %expand ::= rules rhsItems rhsItem alternates
    %ignore ::= '::=' '|' '$'
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

extparserParserConfig = r"""
    /* comment :) */
    ExtParseRules ::= rule *
    rule ::= identifier '::=' alternate ('|' alternate) *
           | configType '::=' (identifier | sqString) + /* nested | just like regex!! */
    alternate ::= '$' | rhsItem +
    rhsItem ::= itemValue ('?' | '+' | '*') ?
    itemValue ::= identifier | sqString | '(' alternate ('|' alternate) * ')'
    %ignore ::= '::=' '|' '$' '(' ')'
"""
extparserParser = makeExtparser(extparserParserConfig)
realOutput = _extparserParser.parse(_extparserLexer.parse(extparserParserConfig))
testOutput = extparserParser.parse(_extparserLexer.parse(extparserParserConfig))
assert(str(realOutput) == str(testOutput))

print('YA!')
