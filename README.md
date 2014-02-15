PyDSL
=====

A runtime DSL parser generator for python.

How to
====

<<<<<<< HEAD
* Define Tokens.
=======
1. Define Tokens.
>>>>>>> 7988034a551cd5c58ccf13c96e7826a02aff3895
```python
lexRules = r"""
    identifier ::= "[_a-zA-Z][_a-zA-Z0-9]+"
    number ::= "[0-9]+(\\.[0-9]+)?"
    operator ::= "[\\+\\-\\*/]"
"""
```
<<<<<<< HEAD
* Define Rules.
=======

2. Define Rules.
>>>>>>> 7988034a551cd5c58ccf13c96e7826a02aff3895
```python
parseRules = r"""
    expression ::= operand (operator operand)*
    operand ::= identifier | number
    %expand ::= operand
"""
```
<<<<<<< HEAD
* Create Lexer and Parser
=======

3. Create Lexer and Parser
>>>>>>> 7988034a551cd5c58ccf13c96e7826a02aff3895
```python
import DSL
lexer = DSL.makeLexer(lexRules)
parser = DSL.makeParser(parseRules)
```
<<<<<<< HEAD
* Use it!!
=======

4. Use it!!
>>>>>>> 7988034a551cd5c58ccf13c96e7826a02aff3895
```python
data = open("source", "r").read()
tokens = lexer.parse(data)
ast = parser.parse(tokens)
# do things with ast
```
