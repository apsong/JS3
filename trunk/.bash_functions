#!/bin/bash
go()
{
    if [ $# -eq 0 ]; then
        cd
    elif [ -d $1 ]; then
        cd $1
    else
        cd `dirname $1`
    fi
}
PS1()
{
    case "$PS1" in
        *\w*)
            PS1=`echo "$PS1" | sed -e 's@\w@\W@'`
            ;;
        *\W*)
            PS1=`echo "$PS1" | sed -e 's@\W@\w@'`
            ;;
    esac
}

tryalias()
{
    [ "$1" = tryalias ] && { echo "Error: Cannot tryalias to itself!" 1>&2; return;}

    local IFS=:
    for p in $PATH; do
        [ -f "$p/$2" ] && { alias $1=$2; break;}
    done
}
tryalias vi vim
tryalias more less
tryalias mail mailx

_DIR_STACK_LENGTH=20
_DIR_STACK_BASE=0
_DIR_STACK_CUR=0
_DIR_STACK_TOP=0
_DIR_STACK_DEBUG=0
builtin_cd()
{
    if [ -z "$1" ]; then
        builtin cd
    else
        builtin cd "$1"
    fi
}
cd()
{
    local TD=""
    for ARG; do
        case "$ARG" in
            /*) TD="$ARG";;
            *) [ -z "$TD" ] && TD="$ARG" || TD="$TD/$ARG";;
        esac
    done

    case "$TD" in
        "-")
            if [ "${_DIR_STACK[$_DIR_STACK_CUR]}" != "$PWD" ]; then
                builtin_cd "${_DIR_STACK[$_DIR_STACK_CUR]}"
                [ $_DIR_STACK_DEBUG -eq 1 ] && cd @
                return 0
            fi
            if [ $_DIR_STACK_CUR -eq `expr \( $_DIR_STACK_BASE + 1 \) % $_DIR_STACK_LENGTH` ]; then
                echo "Error: Already reach the _DIR_STACK_BASE!" 1>&2
                return 1
            fi
            _DIR_STACK_CUR=`expr \( $_DIR_STACK_CUR + $_DIR_STACK_LENGTH - 1 \) % $_DIR_STACK_LENGTH`
            builtin_cd "${_DIR_STACK[$_DIR_STACK_CUR]}"
            [ $_DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
        "+")
            if [ $_DIR_STACK_CUR -eq $_DIR_STACK_TOP ]; then
                echo "Error: Already reach the _DIR_STACK_TOP!" 1>&2
                return 1
            fi
            _DIR_STACK_CUR=`expr \( $_DIR_STACK_CUR + 1 \) % $_DIR_STACK_LENGTH`
            builtin_cd "${_DIR_STACK[$_DIR_STACK_CUR]}"
            [ $_DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
        "!")
            if [ $_DIR_STACK_DEBUG -eq 1 ]; then
                _DIR_STACK_DEBUG=0
                echo "_DIR_STACK_DEBUG is off."
            else
                _DIR_STACK_DEBUG=1
                echo "_DIR_STACK_DEBUG is on."
                cd @
            fi
            ;;
        @*)
            INDEX="${1:1}"
            if [ -z "$INDEX" ]; then #1. No index => Dump current stack
                #echo " TOP: $_DIR_STACK_TOP"
                #echo " CURRENT: $_DIR_STACK_CUR"
                #echo " BASE: `expr \( $_DIR_STACK_BASE + 1 \) % $_DIR_STACK_LENGTH`"
                [ $_DIR_STACK_BASE -eq $_DIR_STACK_TOP ] && return
                i=$_DIR_STACK_BASE
                while [ $i -ne $_DIR_STACK_TOP ]; do
                    j=`expr \( $i + 1 \) % $_DIR_STACK_LENGTH`
                    if [ $j -eq $_DIR_STACK_CUR ]; then
                        echo -e " @ $j:\t${_DIR_STACK[$j]}"
                    else
                        echo -e " $j:\t${_DIR_STACK[$j]}"
                    fi
                    i=`expr \( $i + 1 \) % $_DIR_STACK_LENGTH`
                done
            elif [ "$INDEX" = "S" ]; then #2. @S => Save current stack into file
                cd @ > ~/.cd_history
                case "$PWD" in
                    /|$HOME)
                        echo "$PWD" >> ~/.cd_history
                        ;;
                esac
            elif [ "$INDEX" = "L" ]; then #3. @L => Load current stack from file
                TMP_DIRS=`awk '{print $NF}' ~/.cd_history`
                [ -z "$TMP_DIRS" ] && return 1
                for dir in $TMP_DIRS; do
                    echo " #!CMD:[cd $dir]"
                    cd $dir
                done
            elif [ $_DIR_STACK_BASE -le $_DIR_STACK_TOP -a $_DIR_STACK_BASE -le $INDEX -a $INDEX -le $_DIR_STACK_TOP ] ||
                [ $_DIR_STACK_BASE -gt $_DIR_STACK_TOP -a \( \( 0 -le $INDEX -a $INDEX -le $_DIR_STACK_TOP \) -o \( $_DIR_STACK_BASE -le $INDEX -a $INDEX -lt $_DIR_STACK_LENGTH \) \) ]; then #4. Valid index => GOTO it
                _DIR_STACK_CUR=$INDEX
                builtin_cd "${_DIR_STACK[$_DIR_STACK_CUR]}"
                [ $_DIR_STACK_DEBUG -eq 1 ] && cd @
            else #5. Invalid index => Error message
                echo "Error: Invalid _DIR_STACK_INDEX:[$INDEX]!" 1>&2
                cd @
            fi
            ;;
        *)
            builtin_cd "$TD" || { [ $_DIR_STACK_DEBUG -eq 1 ] && cd @; return;}
            case "$PWD" in
                ${_DIR_STACK[$_DIR_STACK_CUR]}|/|$HOME)
                    [ $_DIR_STACK_DEBUG -eq 1 ] &&
                        { echo " Note: Same dir, root dir, home dir won't be pushed into _DIR_STACK."; cd @;}
                    return
                    ;;
            esac

            if [ "${_DIR_STACK[$_DIR_STACK_TOP]}" = "$PWD" ]; then
                _DIR_STACK_CUR=$_DIR_STACK_TOP
            else
                _DIR_STACK_TOP=`expr \( $_DIR_STACK_TOP + 1 \) % $_DIR_STACK_LENGTH`
                _DIR_STACK_CUR=$_DIR_STACK_TOP
                _DIR_STACK[$_DIR_STACK_CUR]="$PWD"
                [ $_DIR_STACK_TOP -eq $_DIR_STACK_BASE ] &&
                    _DIR_STACK_BASE=`expr \( $_DIR_STACK_BASE + 1 \) % $_DIR_STACK_LENGTH`
            fi
            [ $_DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
    esac
}

_PATH_refine() {
    local P _P _PATH= IFS=:
    for P in $PATH; do
        for _P in $_PATH; do
            [ "$P" = "$_P" ] && continue 2  #P already exists in _PATH, continue with next P
        done
        [ -z "$_PATH" ] && _PATH="$P" || _PATH="$_PATH:$P"
    done
    export PATH="$_PATH"
}
_PATH_insert() {
    local D _PATH=
    for D; do
        [ -d "$D" ] && _PATH=$_PATH:$D
    done
    export PATH=$_PATH:$PATH
    _PATH_refine
}

_PATH_refine
[ -z "$GREP_OPTIONS" ] && export GREP_OPTIONS=--color=auto
export PS1='[\u@\h]\w> '
