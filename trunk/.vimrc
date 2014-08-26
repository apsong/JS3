set nu
set cin
set ts=4
set sw=4
set et
set hls
syntax on
set showmatch
set matchtime=1
set backspace=2
set backupdir=/tmp/vim-tmp,.
set directory=/tmp/vim-tmp,.

if !has("gui_running")
    set t_Co=8
    set t_Sf=1%dm
    set t_Sb=1%dm
endif

autocmd BufReadPost *
    \ if line("'\"")>0&&line("'\"")<=line("$") |
    \ exe "normal g'\"" |
    \ endif

