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
