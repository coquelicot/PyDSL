# PyDSL

A runtime DSL parser generator for python.

## How to

* Define Tokens.
```python
lexRule = r"""#dsl
    identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
    number ::= /[0-9]+(\\.[0-9]+)?/
    operator ::= /[+*\/-]/
"""
```
* Define Rules.
```python
parseRule = r"""#dsl
    expression ::= operand (operator operand)*
    operand ::= identifier | number
    %expand ::= operand
"""
```
* Create Lexer and Parser
```python
import DSL
lexer = DSL.makeLexer(lexRule)
parser = DSL.makeParser(parseRule)
```
* Use it!!
```python
data = open("source", "r").read()
tokens = lexer.parse(data)
ast = parser.parse(tokens)
# do things with ast
```

## Candy

In many cases, you can use `makeDSL` instead of `makeLexer` and `makeParser`.

```python
import DSL
dsl = DSL.makeDSL(r"""#dsl
    identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
    number ::= /[0-9]+(\\.[0-9]+)?/
    operator ::= /[+*\/-]/
    expression ::= operand (operator operand)*
    operand ::= identifier | number
    %expand ::= operand
""")
#parser.parse(lexer.parse(data))
dsl.parse(data)
```

## Syntax Definition

* Lexer DSL's lexer in Lexer DSL
```
%keys ::= '%ignore' '%keys' '::='
comment ::= /#[^\n]*\n/
identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
sqString ::= /'[^']*'/
dqString ::= /"[^"\\]*(\\\\.[^"\\]*)*"/
reString ::= /\/[^\/\\]*(\\\\.[^\/\\]*)*\//
%ignore ::= comment
```
* Lexer DSL's parser in Parser DSL
```
LexRules ::= rule*
rule ::= identifier '::=' (sqString | dqString | reString)
       | '%keys' '::=' (sqString | dqString)+
       | '%ignore' '::=' (identifier | sqString | dqString)+
%ignore ::= '::='
```

* Parser DSL's lexer in Lexer DSL
```
%keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
configType ::= /%(ignore|expandSingle|expand)/
sqString ::= /'[^']*'/
dqString ::= /"[^"\\]*(\\\\.[^"\\]*)*"/
comment ::= /#[^\n]*\n/
%ignore ::= comment
```
* Parser DSL's parser in Parser DSL
```
ParseRules ::= rule*
rule ::= identifier '::=' alternate ('|' alternate)*
       | configType '::=' simpleItem+
alternate ::= '$' | rhsItem+
rhsItem ::= itemValue ('?' | '+' | '*')?
itemValue ::= simpleItem | '(' alternate ('|' alternate)* ')'
simpleItem ::= identifier | dqString | sqString
%ignore ::= '::=' '|' '$' '(' ')'
%expand ::= simpleItem
```
* DSL DSL's lexer in Lexer DDSL
```
%keys ::= '$' '|' '::=' '(' ')' '*' '+' '?'
identifier ::= /[_a-zA-Z][_a-zA-Z0-9]*/
sqString ::= /'[^']*'/
dqString ::= /"[^"\\]*(\\\\.[^"\\]*)*"/
reString ::= /\/[^\/\\]*(\\\\.[^\/\\]*)*\//
configType ::= /%(ignore|expandSingle|expand)/
comment ::= /#[^\n]*\n/
%ignore ::= comment
```
* DSL DSL's parser in Parser DSL
```
DSLRules ::= rule*
rule ::= identifier '::=' reString
       | identifier '::=' alternate ('|' alternate)*
       | configType '::=' simpleItem+
alternate ::= '$' | rhsItem+
rhsItem ::= itemValue ('?' | '+' | '*')?
itemValue ::= simpleItem | '(' alternate ('|' alternate)* ')'
simpleItem ::= identifier | dqString | sqString
%ignore ::= '::=' '|' '$' '(' ')'
%expand ::= simpleItem
```

## Examples

A simple calculator.
```python
import DSL
import functools

lexer = DSL.makeLexer(r"""#dsl
    # It's okay to put comment here
    %keys ::= '+' '*' '(' ')'
    # Be careful!! backslash will be escaped twice!!
    # (and thrice if you're not using raw string)
    # what makeLexer get is
    #  /[0-9]+(\\\\.[0-9]+)?/
    # what it pass to regex recognizer is (escape 1)
    #  [0-9]+(\\.[0-9]+)?
    # the regex recognizer will regard it as (escape 2)
    #  mutiple(digit) one_or_no(backslash anychar multiple(digit))
    number ::= /[0-9]+(\\.[0-9]+)?/
    # makeLexer get
    #  /\/\\*[^\\*]*(\\*+[^*\/][^*]*)*\\*+\//
    # regex get
    #  /\*[^\*]*(\*+[^*/][^*]*)*\*+/
    # note that there's no escape in character set [ ]
    # so, the backslash in [^\*] won't be interpret as escape
    # what it means is "anything but star or backslash"
    comment ::= /\/\\*[^\\*]*(\\*+[^*\/][^*]*)*\\*+\//
    # Remove comment from token stream.
    %ignore ::= comment
""")
parser = DSL.makeParser(r"""#dsl
    # You may use brace, *, +, ? just like regex.
    exprAdd ::= exprMul ('+' exprMul)*
    exprMul ::= term ('*' term)*
    term ::= '(' exprAdd ')' | number
    # Remove them from AST
    %ignore ::= '(' ')' '+' '*'
    # Expand the node if it has only one child
    %expandSingle ::= exprAdd exprMul
    # Always expand the node
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

data = """
    /* The result should be 32.5 */
    1+(2.3+4)*5
"""
tokens = lexer.parse(data)
ast = parser.parse(tokens)
print(evaluateAST(ast))
```

Json-like parser.
```python
import DSL

jsonDSL = DSL.makeDSL(r"""#dsl
    # Remember, it will be escaped twice
    # makeDSL get
    #  /"[^"\\]*(\\\\.[^"\\]*)*"/
    # regex get
    #  "[^"\]*(\\.[^"\]*)*"
    # blackslash will be interpret as escape as long as it's not in []
    # hence, the double blackslash will be interpret as "a blackslash"
    # the meaning of the regex will be
    # " many_or_no(except " \) many_or_no(blackslash anychar many_or_no(except " \)) "
    string ::= /"[^"\\]*(\\\\.[^"\\]*)*"/
    number ::= /[0-9]+(\\.[0-9])?/

    object ::= '{' (kvPair (',' kvPair)*)? '}' # Nested brace!!
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
print(jsonDSL.parse(data))
```
