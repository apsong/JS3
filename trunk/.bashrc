echo "########## source $HOME/.bash_functions ##########"
source $HOME/.bash_functions

export PS1="\033[0;36m[\u]\w>\033[m "
export JAVA_HOME=/usr/java/jdk1.7.0_60
export JS_HOME=$HOME/.JS
export PATH=$JAVA_HOME/bin:/opt/apache-maven-3.2.1/bin:$JS_HOME/bin:$PATH

[ "$HOSTNAME" != "jinsong" ] && export LANG=C

alias ls='ls --color=auto'
alias l.='ls -d .*'
alias ll='ls -l'
alias h='history'
alias js='cd $HOME/.JS/bin'
alias .h='cd $HOME/HSIM/bin'
alias .t='cd $HOME/TRACE/bin'
alias vi='vim'

####################### reset PATH ###########################
_PATH=
IFS=:
for P in $PATH; do
_EXIST=0
    for _P in $_PATH; do
if [ "$P" = "$_P" ]; then
_EXIST=1; break
fi
done
if [ "$_EXIST" -ne 1 ]; then
_PATH="$_PATH:$P"
    fi
done
unset IFS
export PATH="$_PATH"

unset TZ