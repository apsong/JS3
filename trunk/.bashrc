[ -z "$SSH_CLIENT" ] && echo "########## source $HOME/.bash_functions ##########"
source $HOME/.bash_functions
[ -z "$SSH_CLIENT" ] && echo "########## source $HOME/.bash_ds_functions #######"
source $HOME/.bash_ds_functions
source $HOME/.bash_ccb_functions

export PS1="[\u@\h]\w> "
export JAVA_HOME=/opt/jdk
export JS_HOME=$HOME/.JS
export PATH=$JAVA_HOME/bin:/opt/apache-maven-3.3.3/bin:$JS_HOME/bin:$JS_HOME/tea:$JS_HOME/py:$PATH
export PATH=/opt/mysql/bin:$PATH
export PATH=/opt/pypy3/bin:$PATH
export PATH=$HOME/.bin:$PATH
[ -d /CCB/BASE/modules/hadoop ] && export PATH=`ls -d /CCB/BASE/modules/hadoop/hadoop-*/bin`:$PATH

[ "$HOSTNAME" != "jinsong" ] && export LANG=C

alias ls='ls --color=auto'
alias l.='ls -d .*'
alias ll='ls -l'
alias h='history'
alias js='cd $HOME/.JS/bin'
alias tea='cd $HOME/.JS/tea'
alias py='cd $HOME/.JS/py'
alias vi='vim'
alias jp='underscore print --color'

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
ulimit -c unlimited
ulimit -u 10240

export MAVEN_OPTS="-Dmaven.artifact.threads=10 -Xmx2g -XX:MaxPermSize=512M -XX:ReservedCodeCacheSize=512m"
