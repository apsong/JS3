#!/bin/bash

set -e -o pipefail

# Directories from which the *.gz and *.dat will be fetched
SRC_DIR=/home/ap/dip/file/input/p1000/000000000/data

# Writable directories for us to unzip the files and save logs
WORK_DIR=/tmp/ccb.test

ADD_MAP="
    P1000_101008_000000000_ALLYCARD_CUST_INFO_ADD_:AllyCardCustomerInfo_ADD_
     P1000_101008_000000000_FASTPAY_SHOP_INFO_ADD_:FastPayShopInfo_ADD_
          P1000_101008_000000000_QQ_CUST_INFO_ADD_:QQCustomerInfo_ADD_
        P1000_101008_000000000_PRIV_ACCT_INFO_ADD_:CustAccInfos_ADD_
    P1000_101008_000000000_CAS_PRIV_CUST_INFO_ADD_:CustInfos_ADD_
     P1000_101008_000000000_POS_TBL_MCHT_INFO_ADD_:TradFlowMerchantInfo_ADD_
      P1000_101008_000000000_POS_TBL_MCHT_SRE_ADD_:merchantInfo_ADD_

      P1000_101008_000000000_ALLYCARD_TRAD_FLOW_ADD_:AllyTradeFlow_ADD_
       P1000_101008_000000000_FASTPAY_TRAD_FLOW_ADD_:FastPayTradFlow_ADD_
            P1000_101008_000000000_QQ_TRAD_FLOW_ADD_:QQTradeFlow_ADD_
    P1000_101008_000000000_ECTIP_PRIV_TRAD_FLOW_ADD_:TradFlowDetails_ADD_
         P1000_101008_000000000_ECTIP_TRAD_FLOW_ADD_:TradFlows_ADD_
       P1000_101008_000000000_POS_POSB_TXN_LIST_ADD_:posFlow_ADD_

    P1000_101008_000000000_CUST_ACTION_REPORT_ADD_:CustWhiteList_ADD_
"
ALL_MAP="
    P1000_101008_000000000_ALLYCARD_CUST_INFO_ALL_:AllyCardCustomerInfo_ALL_
     P1000_101008_000000000_FASTPAY_SHOP_INFO_ALL_:FastPayShopInfo_ALL_
          P1000_101008_000000000_QQ_CUST_INFO_ALL_:QQCustomerInfo_ALL_
        P1000_101008_000000000_PRIV_ACCT_INFO_ALL_:CustAccInfos_ALL_
    P1000_101008_000000000_CAS_PRIV_CUST_INFO_ALL_:CustInfos_ALL_
     P1000_101008_000000000_POS_TBL_MCHT_INFO_ALL_:TradFlowMerchantInfo_ALL_
      P1000_101008_000000000_POS_TBL_MCHT_SRE_ALL_:merchantInfo_ALL_

      P1000_101008_000000000_ALLYCARD_TRAD_FLOW_ALL_:AllyTradeFlow_ALL_
       P1000_101008_000000000_FASTPAY_TRAD_FLOW_ALL_:FastPayTradFlow_ALL_
            P1000_101008_000000000_QQ_TRAD_FLOW_ALL_:QQTradeFlow_ALL_
    P1000_101008_000000000_ECTIP_PRIV_TRAD_FLOW_ALL_:TradFlowDetails_ALL_
         P1000_101008_000000000_ECTIP_TRAD_FLOW_ALL_:TradFlows_ALL_
       P1000_101008_000000000_POS_POSB_TXN_LIST_ALL_:posFlow_ALL_

"
#    P1000_101008_000000000_CUST_ACTION_REPORT_ALL_:CustWhiteList_ALL_
DAILY_MAP="
    P1000_101008_000000000_ALLYCARD_CUST_INFO_ADD_:AllyCardCustomerInfo_ADD_
      P1000_101008_000000000_ALLYCARD_TRAD_FLOW_ALL_:AllyTradeFlow_ALL_
"
######################### LOG ##########################################
PROGRAM=`basename $0`
LOG=$WORK_DIR/.$PROGRAM.log
touch $LOG

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

######################### SEQ_YYYYMMDD #################################
seq_yyyymmdd()
{
    [ `expr "$1" : '[0-9]\+'` -ne 8 ] && { "'$1' should be of format 'yyyymmdd'"; exit 1;}
    [ `expr "$2" : '[0-9]\+'` -ne 8 ] && { "'$2' should be of format 'yyyymmdd'"; exit 1;}
    date -d "$1" >/dev/null || exit 1
    date -d "$2" >/dev/null || exit 1

    END=`date -d "$2" +%Y%m%d`
    DAY=`date -d "$1" +%Y%m%d`
    while [ $DAY -le $END ]; do
        echo $DAY
        DAY=`date -d "$DAY +1 day" +%Y%m%d`
    done
}
######################### MAIN #########################################
usage()
{
    echo 1>&2 "Usage: $PROGRAM {ADD|ALL} [DATE_BEGIN] [DATE_END]"
    echo 1>&2
    echo 1>&2 " Sample:"
    echo 1>&2 "       $PROGRAM ADD 20150101 20150630 --fetch 'ADD' data of the half year"
    echo 1>&2 "       $PROGRAM ADD 20150630          --fetch 'ADD' data of day 20150630"
    echo 1>&2 "       $PROGRAM ADD                   --fetch 'ADD' data of yesterday"
    echo 1>&2 " Note: 'ADD' and 'ALL' are the CCB filename style,"
    echo 1>&2 "       which represents INCREMENTAL and TOTAL data respectively."
}

#a. Azkaban input parameter 'unzipdate'
azkb_unzipdate=`find -name "*_props_*" -exec awk -F= '/unzipdate/{print $2}' {} \; | tail -1`
azkb_unzipdate_begin=`echo $azkb_unzipdate | awk '{print $1}'`
azkb_unzipdate_end=`echo $azkb_unzipdate | awk '{print $NF}'`
logDEBUG "Azkaban input parameter: unzipdate=$azkb_unzipdate"

#b. yesterday
yesterday=`date -d '-1 day' +%Y%m%d`
logDEBUG "yesterday=$yesterday"

#1. Choose which file map to use depending on $1 (the first parameter: 'ADD', 'ALL')
[ $# -eq 0 ] && { usage; exit 1;}
map=${1}_MAP
MAP=${!map}
#1. Set unzipdate
unzipdate_begin=$2
unzipdate_end=$3
[ -z "$unzipdate_begin" ] && { unzipdate_begin=$azkb_unzipdate_begin; unzipdate_end=$azkb_unzipdate_end; }
[ -z "$unzipdate_begin" ] && { unzipdate_begin=$yesterday; unzipdate_end=$yesterday;}
[ -z "$unzipdate_end" ]   && { unzipdate_end=$unzipdate_begin;}
logDEBUG "Finally: use map=\$$map unzipdate_begin=$unzipdate_begin unzipdate_end=$unzipdate_end"

#2. Validate unzipdate
for DAY in $unzipdate_begin $unzipdate_end; do
    if [ `expr "$DAY" : '[0-9]\+'` -ne 8 ]; then
        echo 1>&2 "Error: unzipdate '$DAY' should be of format '$yesterday'"
        exit 2
    fi
done

#3. remove unzipped files which have been done processing
DONE_DIR="$WORK_DIR/.done"
mkdir -p $DONE_DIR
find $WORK_DIR -maxdepth 1 -type f -name "*.done" -exec mv {} $DONE_DIR \;
find $DONE_DIR -type f -ctime 30 -exec rm -f {} \;

#4. Rotate log to keep no more than 20000 lines
if [ `cat $LOG | wc -l` -gt 20000 ]; then
    LOG_BAK=$LOG.`date +%Y%m%d-%H%M%S`
    mv $LOG $LOG_BAK
    log "(log archived into $LOG_BAK)"
fi

#5. Unzip
for DAY in `seq_yyyymmdd $unzipdate_begin $unzipdate_end`; do
    [ ! -d $SRC_DIR/$DAY ] && { log "Warning: No directory '$SRC_DIR/$DAY'"; continue;}
    for KV in $MAP; do
        CCB_PATTERN=`echo $KV | awk -F: '{print $1}'`${DAY}_
        NEW_PATTERN=`echo $KV | awk -F: '{print $2}'`${DAY}_
        num=0
        for CCB_PATH in `find $SRC_DIR/$DAY -maxdepth 1 -type f -regex ".*/$CCB_PATTERN[^_]+"`; do
            case $CCB_PATH in
                *.gz)
                    NEW_PATH=$WORK_DIR/`basename $CCB_PATH | sed -e "s/$CCB_PATTERN/$NEW_PATTERN/" -e 's/\.gz$//'`
                    log "$CCB_PATH => $NEW_PATH"
                    { gunzip -c $CCB_PATH | sed -e 's/|@|/|/g' >$NEW_PATH; } 2>>$LOG;;
                *.dat)
                    NEW_PATH=$WORK_DIR/`basename $CCB_PATH | sed -e "s/$CCB_PATTERN/$NEW_PATTERN/"`
                    log "$CCB_PATH -> $NEW_PATH"
                    { cat       $CCB_PATH | sed -e 's/|@|/|/g' >$NEW_PATH; } 2>>$LOG;;
            esac
            num=`expr $num + 1`
        done
        [ $num -eq 0 ] && log "Warning: No file like '$SRC_DIR/$DAY/$CCB_PATTERN[^_]+'"
    done
done
