PyDSL
=====

A runtime DSL parser generator for python.

How to
====

* Define Tokens.
```python
lexRules = r"""
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]+"
    number ::= "[0-9]+(\\.[0-9]+)?"
    operator ::= "[\\+\\-\\*/]"
"""
```
* Define Rules.
```python
parseRules = r"""
    expression ::= operand (operator operand)*
    operand ::= identifier | number
    %expand ::= operand
"""
```
* Create Lexer and Parser
```python
import DSL
lexer = DSL.makeLexer(lexRules)
parser = DSL.makeParser(parseRules)
```
* Use it!!
```python
data = open("source", "r").read()
tokens = lexer.parse(data)
ast = parser.parse(tokens)
# do things with ast
```

Syntax Definition
====

* Lexer DSL's lexer in Lexer DSL
```
%keys ::= '%ignore' '%keys' '::='
identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
dqString ::= "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""
comment ::= "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/"
%ignore ::= comment
```
* Lexer DSL's parser in Parser DSL
```
LexRules ::= rule*
rule ::= identifier '::=' (sqString | dqString)
       | '%keys' '::=' sqString+
       | '%ignore' '::=' (identifier | sqString)+
%ignore ::= '::='
```

* Parser DSL's lexer in Lexer DSL
```
%keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
identifier ::= "[_a-zA-Z][_a-zA-Z0-9]*"
configType ::= "%(ignore|expandSingle|expand)"
sqString ::= "'[^'\\\\]*(\\\\.[^'\\\\]*)*'"
comment ::= "/\\*[^\\*]*(\\*+[^/\\*][^\\*]*)*\\*+/"
%ignore ::= comment
```
* Parser DSL's parser in Parser DSL
```
ParseRules ::= rule*
rule ::= identifier '::=' alternate ('|' alternate)*
       | configType '::=' (identifier | sqString)+
alternate ::= '$' | rhsItem+
rhsItem ::= itemValue ('?' | '+' | '*')?
itemValue ::= identifier | sqString | '(' alternate ('|' alternate)* ')'
%ignore ::= '::=' '|' '$' '(' ')'
```

Examples
====

A simple calculator.
```python
import DSL
import functools

lexer = DSL.makeLexer(r"""
    /* It's okay to put comment here */
    %keys ::= '+' '*' '(' ')'
    /* Be careful!! backslash will be escaped!! */
    number ::= "[0-9]+(\\.[0-9]+)?"
""")
parser = DSL.makeParser(r"""
    /* You may use brace, *, +, ? just like regex. */
    exprAdd ::= exprMul ('+' exprMul)*
    exprMul ::= term ('*' term)*
    term ::= '(' exprAdd ')' | number
    /* Remove them from AST */
    %ignore ::= '(' ')' '+' '*'
    /* Expand the node if it has only one child */
    %expandSingle ::= exprAdd exprMul
    /* Always expand the node */
    %expand ::= term
""")

def evaluateAST(ast):
    if ast.name == 'number':
        return float(ast.value) if '.' in ast.value else int(ast.value)
    else:
        if ast.name == 'exprAdd':
            func = lambda a, b: a + b
        else:
            func = lambda a, b: a * b
        return functools.reduce(func, map(evaluateAST, ast.child))

data = "1+(2.3+4)*5"
tokens = lexer.parse(data)
ast = parser.parse(tokens)
print(evaluateAST(ast))
```

Json-like parser.
```python
import DSL

lexer = DSL.makeLexer(r"""
    %keys ::= '{' '}' '[' ']' ':' ',' 'true' 'false' 'null'
    string ::= "\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\""
    number ::= "[0-9]+(\\.[0-9])?"
""")
parser = DSL.makeParser(r"""
    object ::= '{' (kvPair (',' kvPair)*)? '}' /* Nested brace!! */
    kvPair ::= string ':' value
    array ::= '[' (value (',' value)*)? ']'
    value ::= string | number | object | array | 'true' | 'false' | 'null'
    %ignore ::= '{' '}' '[' ']' ',' ':'
    %expand ::= value
""")

data = r"""
{
    "key1" : {
        "key2" : [1, 2, 3, 4],
        "key3" : [
            {},
            { "key4" : "value" }
        ]
    },
    "key5" : null,
    "key6" : [
        [1, 2, 3],
        [4.4, 5.5, 6.6],
        ["string", 8, 9.9],
        true
    ]
}
"""
print(parser.parse(lexer.parse(data)))
```
