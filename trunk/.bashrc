[ -z "$SSH_CLIENT" ] && echo "########## source $HOME/.bash_functions ##########"
source $HOME/.bash_functions
#[ -z "$SSH_CLIENT" ] && echo "########## source $HOME/.bash_ds_functions #######"
#source $HOME/.bash_ds_functions
#source $HOME/.bash_ccb_functions

export PS1="[\u@\h]\w> "
export JAVA_HOME=/opt/jdk
export JS_HOME=$HOME/.JS
export PATH=$JAVA_HOME/bin:/opt/apache-maven-3.3.3/bin:$JS_HOME/bin:$JS_HOME/tea:$JS_HOME/py:$PATH
export PATH=/opt/mysql/bin:$PATH
export PATH=/opt/pypy3/bin:$PATH
export PATH=$HOME/.bin:$PATH
export PATH=/MINE/hadoop-2.6.0/bin:$PATH
export PATH=/opt/sbt/bin:$PATH
_PATH_refine

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

unset TZ
ulimit -c unlimited
ulimit -u 10240

export MAVEN_OPTS="-Dmaven.artifact.threads=10 -Xmx2g -XX:MaxPermSize=512M -XX:ReservedCodeCacheSize=512m"
