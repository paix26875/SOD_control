#!/bin/bash

echo 'Setting up Now .....'
# アーカイブディレクトリが存在しない場合アーカイブディレクトリを作成
if [ ! -d 'archive' ]; then
    mkdir 'archive'
fi

# 前回の実験データが残っている場合、そのデータをアーカイブする
if [ -d 'temp' ]; then
    echo 'Archiving the previous data .....'
    # TODO: windowsだとsedコマンドがないかもしれない
    # 参考：https://qiita.com/hirohiro77/items/7fe2f68781c41777e507
    previous_experiment_date=`sed -n 1p temp/log.csv`
    archive_dir="archive/${previous_experiment_date}"
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

# 今日の実験データの保存先
echo 'Creating new directory .....'
today=`date '+%Y%m%d'`
mkdir 'temp'
cp 'setting.py.example' 'temp/setting.py'
cd 'temp'
touch 'log.log'
echo ${today} > log.log
mkdir 'images'
mkdir 'calibrationimg'
mkdir 'csv'
mkdir 'videos'