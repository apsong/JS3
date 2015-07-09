#!/bin/bash

Azkaban session.reinit || exit 1
for PROJECT_DIR in `find -mindepth 1 -maxdepth 1 -type d -name "[a-zA-Z]*"`; do
    PROJECT=`basename $PROJECT_DIR`
    Azkaban project.create -p $PROJECT
    Azkaban project.upload -p $PROJECT -z $PROJECT_DIR
done
