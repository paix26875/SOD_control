#!/bin/bash

echo 'Setting up Now .....'
if [ ! -d 'archive' ]; then
    mkdir 'archive'
fi

if [ -d 'temp' ]; then
    echo 'Archiving the previous data .....'
    today=`date '+%Y%m%d'`
    archive_dir="archive/${today}"
    if [ -d $archive_dir ]; then
        echo 'Do you want to remove a directory that already exists? [yes/no(recommend)]'
        read answer
        if [ $answer = 'yes' ]; then
            rm -rf $archive_dir
            mv 'temp' $archive_dir
        else
            rm -rf 'temp'
        fi
    else
        mv 'temp' $archive_dir
    fi
fi

echo 'Creating new directory .....'
mkdir 'temp'
cp 'setting.py.example' 'temp/setting.py'
cd 'temp'
mkdir 'images'
mkdir 'calibrationimg'