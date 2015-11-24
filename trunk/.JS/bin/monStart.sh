#!/bin/bash

#Usage: monStart.sh [DELAY (default to 1 second)]
PROGRAM=`basename $0`
LOG=/tmp/$PROGRAM.log
>$LOG
DSTAT_TIMEFMT="%y%m%d %T" exec dstat -t -c -m -d -n --integer --output $LOG "$@" >/dev/null
