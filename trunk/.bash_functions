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

    IFS=:
    for p in $PATH; do
        [ -f "$p/$2" ] && { alias $1=$2; break;}
    done
    unset IFS
}
tryalias vi vim
tryalias more less
tryalias mail mailx

DIR_STACK_LENGTH=20
DIR_STACK_BASE=0
DIR_STACK_CUR=0
DIR_STACK_TOP=0
DIR_STACK_DEBUG=0
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
    TD=""
    for ARG; do
        case "$ARG" in
            /*) TD="$ARG";;
            *) [ -z "$TD" ] && TD="$ARG" || TD="$TD/$ARG";;
        esac
    done

    case "$TD" in
        "-")
            if [ "${DIR_STACK[$DIR_STACK_CUR]}" != "$PWD" ]; then
                builtin_cd "${DIR_STACK[$DIR_STACK_CUR]}"
                [ $DIR_STACK_DEBUG -eq 1 ] && cd @
                return 0
            fi
            if [ $DIR_STACK_CUR -eq `expr \( $DIR_STACK_BASE + 1 \) % $DIR_STACK_LENGTH` ]; then
                echo "Error: Already reach the DIR_STACK_BASE!" 1>&2
                return 1
            fi
            DIR_STACK_CUR=`expr \( $DIR_STACK_CUR + $DIR_STACK_LENGTH - 1 \) % $DIR_STACK_LENGTH`
            builtin_cd "${DIR_STACK[$DIR_STACK_CUR]}"
            [ $DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
        "+")
            if [ $DIR_STACK_CUR -eq $DIR_STACK_TOP ]; then
                echo "Error: Already reach the DIR_STACK_TOP!" 1>&2
                return 1
            fi
            DIR_STACK_CUR=`expr \( $DIR_STACK_CUR + 1 \) % $DIR_STACK_LENGTH`
            builtin_cd "${DIR_STACK[$DIR_STACK_CUR]}"
            [ $DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
        "!")
            if [ $DIR_STACK_DEBUG -eq 1 ]; then
                DIR_STACK_DEBUG=0
                echo "DIR_STACK_DEBUG is off."
            else
                DIR_STACK_DEBUG=1
                echo "DIR_STACK_DEBUG is on."
                cd @
            fi
            ;;
        @*)
            INDEX="${1:1}"
            if [ -z "$INDEX" ]; then #1. No index => Dump current stack
                #echo " TOP: $DIR_STACK_TOP"
                #echo " CURRENT: $DIR_STACK_CUR"
                #echo " BASE: `expr \( $DIR_STACK_BASE + 1 \) % $DIR_STACK_LENGTH`"
                [ $DIR_STACK_BASE -eq $DIR_STACK_TOP ] && return
                i=$DIR_STACK_BASE
                while [ $i -ne $DIR_STACK_TOP ]; do
                    j=`expr \( $i + 1 \) % $DIR_STACK_LENGTH`
                    if [ $j -eq $DIR_STACK_CUR ]; then
                        echo -e " @ $j:\t${DIR_STACK[$j]}"
                    else
                        echo -e " $j:\t${DIR_STACK[$j]}"
                    fi
                    i=`expr \( $i + 1 \) % $DIR_STACK_LENGTH`
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
            elif [ $DIR_STACK_BASE -le $DIR_STACK_TOP -a $DIR_STACK_BASE -le $INDEX -a $INDEX -le $DIR_STACK_TOP ] ||
                [ $DIR_STACK_BASE -gt $DIR_STACK_TOP -a \( \( 0 -le $INDEX -a $INDEX -le $DIR_STACK_TOP \) -o \( $DIR_STACK_BASE -le $INDEX -a $INDEX -lt $DIR_STACK_LENGTH \) \) ]; then #4. Valid index => GOTO it
                DIR_STACK_CUR=$INDEX
                builtin_cd "${DIR_STACK[$DIR_STACK_CUR]}"
                [ $DIR_STACK_DEBUG -eq 1 ] && cd @
            else #5. Invalid index => Error message
                echo "Error: Invalid DIR_STACK_INDEX:[$INDEX]!" 1>&2
                cd @
            fi
            ;;
        *)
            builtin_cd "$TD" || { [ $DIR_STACK_DEBUG -eq 1 ] && cd @; return;}
            case "$PWD" in
                ${DIR_STACK[$DIR_STACK_CUR]}|/|$HOME)
                    [ $DIR_STACK_DEBUG -eq 1 ] &&
                        { echo " Note: Same dir, root dir, home dir won't be pushed into DIR_STACK."; cd @;}
                    return
                    ;;
            esac

            if [ "${DIR_STACK[$DIR_STACK_TOP]}" = "$PWD" ]; then
                DIR_STACK_CUR=$DIR_STACK_TOP
            else
                DIR_STACK_TOP=`expr \( $DIR_STACK_TOP + 1 \) % $DIR_STACK_LENGTH`
                DIR_STACK_CUR=$DIR_STACK_TOP
                DIR_STACK[$DIR_STACK_CUR]="$PWD"
                [ $DIR_STACK_TOP -eq $DIR_STACK_BASE ] &&
                    DIR_STACK_BASE=`expr \( $DIR_STACK_BASE + 1 \) % $DIR_STACK_LENGTH`
            fi
            [ $DIR_STACK_DEBUG -eq 1 ] && cd @
            ;;
    esac
}

