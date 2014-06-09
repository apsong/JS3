#! /bin/sh

for FILE in `ls -A trunk`; do
rm -rf $HOME/$FILE
ln -s -v $PWD/trunk/$FILE $HOME
done
