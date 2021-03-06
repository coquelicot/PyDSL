" Vim syntax file
" Language:	    PyDSL
" Maintainer:	Fcrh <coquelicot1117@gmail.com>
" Last Change:	2014 Feb 17

if exists("b:current_syntax")
  finish
endif

syn match dslIdentifier /[_a-zA-Z][_a-zA-Z0-9]*/
syn match dslOperator /::=\|+\|*\|?\|(\|)\||/
syn match dslKeyword /%\(ignore\|expand\|expandSingle\|keys\)/
syn match dslEscapedChar /\\./
syn match dslComment "#.*$"

syn region dslSqString start="'" end="'"
syn region dslDqString start=+"+ end=+"+ skip=+\\\\\|\\"+ contains=dslEscapedChar
syn region dslReString start="/" end="/" skip=+\\\\\|\\"+ contains=dslEscapedChar

hi def link dslIdentifier Identifier
hi def link dslKeyword Type
hi def link dslSqString String
hi def link dslDqString String
hi def link dslReString String
hi def link dslComment Comment
hi def link dslOperator Operator
hi def link dslEscapedChar SpecialChar

let b:current_syntax = "pydsl"
