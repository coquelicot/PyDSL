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

Examples
====

A simple calculator.
```python
import DSL
import functools

lexer = DSL.makeLexer(r"""
    %keys ::= '+' '*' '(' ')'
    number ::= "[0-9]+(\\.[0-9]+)?"
""")
parser = DSL.makeParser(r"""
    exprAdd ::= exprMul ('+' exprMul)*
    exprMul ::= term ('*' term)*
    term ::= '(' exprAdd ')' | number
    %ignore ::= '(' ')' '+' '*'
    %expandSingle ::= exprAdd exprMul
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
    object ::= '{' (kvPair (',' kvPair)*)? '}'
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
