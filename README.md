# SOD_control

- THIN_WALL_SOD_CONTROL.MPF：NCプログラムのメインファイル
- Inprocess_calcurate_sod_temperature.py：撮影・画像処理・SOD算出・溶融地温度算出を行うファイル
- sod_calibration.py：キャリブレーション処理を行うpythonファイル
- auto_capture.py：ファイル保存のクリック位置を求めるpythonファイル

## セットアップ

1. コマンドプロンプトを起動
2. `make setup`を実行
   - 前回の実験結果をarchive
   - 今回の実験に必要なディレクトリを作成する
     - images
     - calibrationimg
     - setting.py


## ディレクトリ構造

Artviewerによる画像の保存先はpythonファイルと同じ階層のimagesディレクトリに指定する

- Inprocess_calcurate_sod_temperature.py
- sod_calibration.py
- auto_capture.py
- archive
- temp
  - calibrationimg
    - img_0000
    - img_0001
    - ....
  - images
    - img_0000
    - img_0001
    - ....


## R変数の設定

R0：外部PCとCELOSのステータス
|数値|MPF|python|
|-|-|-|
|0|MPFの処理実行中|起動中、MPFによる実行指示待ち|
|1|pythonへの処理開始指示|処理開始のトリガー|
|2|pythonによる処理待ち、造形中|pythonによる処理の実行中|
|3|pythonファイルの処理終了指示|pythonのプログラム終了|

- MPFの最初で`R0=0`として初期化する
- レーザ出力開始時（`M174`）に`R1=1`として、pythonプログラムの処理開始指示を行う
- pythonプログラムは一定時間間隔で`R0`の値を読む。`R0=0`であれば、これを繰り返す
- pythonプログラムは`R0=1`で処理を開始、処理中は`R0=2`とする
- pythonプログラムの処理が完了すると`R0=0`と書き込み処理が終了したことを伝える
- 造形を終了し、pythonプログラムを終了させる場合はMPF側で`R0=3`とする。

R1：積層ピッチ

- pythonにより計算した積層ピッチを入力する
- MPFで積層ピッチを読み取り、`Z=IC()`でレーザヘッドを移動させる

R2：レーザ出力

- pythonにより計算したレーザ出力を入力する
- MPFでレーザ出力を読み取り、`H52=`でレーザ出力を変更する