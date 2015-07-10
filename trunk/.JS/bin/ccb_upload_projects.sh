#!/bin/bash

PROGRAM=`basename $0`
AZKABAN=`dirname $0`/Azkaban

$AZKABAN session.reinit || exit 1
for PROJECT_DIR in `find -mindepth 1 -maxdepth 1 -type d -name "[a-zA-Z]*"`; do
    PROJECT=`basename $PROJECT_DIR`
    $AZKABAN project.create -p $PROJECT
    $AZKABAN project.upload -p $PROJECT -z $PROJECT_DIR
done
