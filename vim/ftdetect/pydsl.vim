autocmd BufNewFile,BufReadPost *.dsl set filetype=pydsl
autocmd BufNewFile,BufReadPost *.py call SnipPyDSL()

function SnipPyDSL() abort

  if exists('b:current_syntax')
    let s:current_syntax=b:current_syntax
    unlet b:current_syntax
  endif
  execute 'syntax include @EmbededPyDSL syntax/pydsl.vim'

  if exists('s:current_syntax')
    let b:current_syntax=s:current_syntax
  else
    unlet b:current_syntax
  endif
  execute 'syntax region SnipPyDSL matchgroup=SpecialComment start=+r"""#dsl+ end=+"""+ contains=@EmbededPyDSL'

endfunction
