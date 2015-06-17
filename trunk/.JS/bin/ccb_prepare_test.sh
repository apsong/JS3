#!/bin/bash

##################### .JS/bin/_SH_UTIL_FUNCTIONS <BEGIN> #######################
EVAL()
{
    echo "#!CMD:[" $@ "]"
    eval "$@"
}
##################### .JS/bin/_SH_UTIL_FUNCTIONS <END> #########################
DIR1="/home/ap/ep/filesvr/files/POS"
FILES1="
    P1000_101008_000000000_POS_FCRSPR4_ADD
    P1000_101008_000000000_POS_POSB_TXN_LIST_ADD
    P1000_101008_000000000_POS_TBL_MCHT_INFO_ADD
    P1000_101008_000000000_POS_TBL_MCHT_SRE_ADD
    P1000_101008_000000000_POS_TBL_MCHT_TERM_INF_ADD
"
DIR2="/home/ap/dip/file/input/p1000/000000000/data"
FILES2="
    P1000_101008_000000000_CAS_ALLYCARD_CUST_INFO_ADD
    P1000_101008_000000000_CAS_ALLYCARD_TRAD_FLOW_ADD
    P1000_101008_000000000_CAS_FASTPAY_SHOP_INFO_ADD
    P1000_101008_000000000_CAS_FASTPAY_TRAD_FLOW_ADD
    P1000_101008_000000000_CAS_PRIV_ACCT_INFO_ADD
    P1000_101008_000000000_CAS_PRIV_CUST_INFO_ADD
    P1000_101008_000000000_CAS_QQ_TRAD_FLOW_ADD
    P1000_101008_000000000_ECTIP2_PRIV_TRAD_FLOW_ADD
    P1000_101008_000000000_ECTIP2_TRAD_FLOW_ADD
"

BEGIN=${1:-20150101}
END=${2:-20150201}
do_prepare()
{
    DIR="$1"
    FILES="$2"
    sudo rm -rf $DIR
    sudo mkdir -p $DIR
    sudo chmod 777 $DIR
    for DAY in `seq_yyyymmdd $BEGIN $END`; do
        mkdir $DIR/$DAY
        for FILE in $FILES; do
            DAT=$DIR/$DAY/${FILE}_$DAY
            echo "DATA: ${FILE}_$DAY" > $DAT
            gzip $DAT
        done
    done
}
do_prepare "$DIR1" "$FILES1"
do_prepare "$DIR2" "$FILES2"
find $DIR1 $DIR2 -type d | sort
echo
EVAL ls $DIR1/$END
echo
EVAL ls $DIR2/$END
