#!/bin/sh

#Directories from which the *.gz will be fetched
SRC_DIRS="
    /home/ap/ep/filesvr/files/POS/
    /home/ap/dip/file/input/p1000/000000000/data/
"
#Writable directories for us to unzip the files and save logs
WORK_DIR=/home/sjin/ccb

######################### LOG ##########################################
PROGRAM=`basename $0`
LOG=$WORK_DIR/.$PROGRAM.log
touch $LOG || exit 1

#0:DEBUG  1:NORMAL
logLEVEL=0
logDEBUG()
{
    [ $logLEVEL -le 0 ] && { NOW=`date "+%Y%m%d-%H:%M:%S"`; echo $NOW [DEBUG] "$@" >> $LOG;}
}
log()
{
    [ $logLEVEL -le 0 ] && { NOW=`date "+%Y%m%d-%H:%M:%S"`; echo $NOW "$@" >> $LOG;}
}

######################### MAIN #########################################
#a. Azkaban input parameter 'unzipdate'
azkb_unzipdate=`find -name "*_props_*" -exec awk -F= '/unzipdate/{print $2}' {} \; | tail -1`
logDEBUG "Azkaban input parameter: unzipdate=$azkb_unzipdate"

#b. Last unzip date from log
last_unzipdate=`awk '/Unzip succeeded:/{print $4}' $LOG 2>/dev/null | tail -1`
[ -n "$last_unzipdate" ] && next_unzipdate=`date -d "$last_unzipdate +1 day" +%Y%m%d`
logDEBUG "From $LOG: last_unzipdate=$last_unzipdate next_unzipdate=$next_unzipdate"

#c. yesterday
yesterday=`date -d '-1 day' +%Y%m%d`
logDEBUG "yesterday=$yesterday"

#1. Set unzipdate
unzipdate=$1
[ -z "$unzipdate" ] && unzipdate=$azkb_unzipdate
[ -z "$unzipdate" ] && unzipdate=$next_unzipdate
logDEBUG "Finally: unzipdate=$unzipdate"

#2. Validate unzipdate
if [ `expr "$unzipdate" : '[0-9]\+'` -ne 8 ]; then
    echo 1>&2 "Error: unzipdate '$unzipdate' should be of format '$yesterday'"
    exit 2
fi
if [ "$unzipdate" -gt "$yesterday" ]; then
    echo 1>&2 "Error: unzipdate '$unzipdate' cannot be greater than yesterday '$yesterday'"
    exit 3
fi

#3. remove unzipped files which have been done processing
find $WORK_DIR -type f -name "*.done" -exec rm -f {} \;

#4. Unzip
DIRS=`find $SRC_DIRS -type d -name $unzipdate`
if [ -z "$SRC_DIRS" ]; then
    echo 1>&2 "Error: cannot find directory '$unzipdate' in '$SRC_DIRS'"
    exit 4
fi
GZ_FILES=`find $DIRS -name "*.gz"`
log "Unzip started: $unzipdate"
i=0
for GZ_FILE in $GZ_FILES; do
    UNZIP_FILE=$WORK_DIR/`basename $GZ_FILE | sed -e 's/\.gz$//'`
    if [ ! -f "$UNZIP_FILE" ]; then
        logDEBUG "gunzip -c $GZ_FILE > $UNZIP_FILE"
        gunzip -c $GZ_FILE > $UNZIP_FILE || exit 5
    fi
    i=`expr $i + 1`
done
log "Unzip succeeded: $unzipdate ($i files)"

##################################################################
# Rotate log to keep no more than 20000 lines
if [ `cat $LOG | wc -l` -gt 20000 ]; then
    mv $LOG $LOG.bak
    log "(log truncated)"
    tail -10000 $LOG.bak >> $LOG
    rm $LOG.bak
fi
