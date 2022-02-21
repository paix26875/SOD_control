from PIL import Image
import numpy as np
import cv2
from icecream import ic
import time
import matplotlib.pyplot as plt
import os
import datetime
import csv
import glob
from opcua import Client, ua
import pyautogui
import sys

# numpyの配列表示数の設定
np.set_printoptions(threshold=np.inf)


def set_Rvalue(client, Rnumber, value):
    '''
    R変数に値をセットする関数

    Parameters
    ----------
    client : 
    Rnumber : int
        値をセットするR変数の番号
    value : int
        R変数にセットする値
    '''
    # TODO: clientの渡し方が適切なのかチェックする
    R = client.get_node('ns=2;s=/Channel/Parameter/R[' + str(Rnumber) + ']')
    V = ua.Variant(value, ua.VariantType.Double)
    R.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(V))
    pass
# R変数の値を読み込む関数
def get_Rvalue(client, Rnumber):
    R = client.get_node('ns=2;s=/Channel/Parameter/R[' + str(Rnumber) + ']')
    r = R.get_value()
    return r

def get_gravitypoint_CMOS(img_color, show_gp_img = True, threshold = 20, print_gp = True, trimheight=300, trimwidth=300):
    """
    画像の輪郭から重心を求める(CMOS画像用)

    Parameters
    ----------
    img_color : numpy
        画像のRGB値が入った配列
    show_gp_img : bool
        重心を表示した画像を表示するかどうか
    threshold : int
        二値化する際の閾値
    print_gp : bool
        計算した重心座標を出力するかどうか
    trimheight : int
        トリミングする画像の高さ
    trimwidth : int
        トリミングする画像の幅
    
    Returns
    -------
    gravitypoint_x : int
        重心のx座標
    gravitypoint_y : int
        重心のy座標
    """
    h,w,l = img_color.shape
    img_red = img_color[:,:,0]
    ret, img_thresh = cv2.threshold(img_red, threshold, 255, cv2.THRESH_BINARY)

    mu = cv2.moments(img_thresh, False)
    if mu["m00"] == 0:
        gravitypoint_x = int(w / 2)
        gravitypoint_y = int(h / 2)
        return gravitypoint_x, gravitypoint_y
    gravitypoint_x, gravitypoint_y= int(mu["m10"]/mu["m00"]) , int(mu["m01"]/mu["m00"])

    if show_gp_img == True:
        # 重心を画像で表示
        cv2.circle(img_thresh, (gravitypoint_x, gravitypoint_y), 1, 100, 1, 3)
        plt.imshow(img_thresh)
        plt.colorbar()
        plt.show()
    if print_gp:
        ic(gravitypoint_x, gravitypoint_y)
    if gravitypoint_y > (h - trimheight/2) or gravitypoint_x < (trimwidth/2 + 1) :
        gravitypoint_x = int(w / 2)
        gravitypoint_y = int(h / 2)
        return gravitypoint_x, gravitypoint_y
    return gravitypoint_x, gravitypoint_y


if __name__ == '__main__':
    # 定数の設定
    number_of_images = 3
    height = 300
    width = 300
    threshold = 20
    coefs = np.array([ 2.15489147e+00, -1.50682127e+00,  6.00025683e+00,  1.77044939e+03])

    number_of_tracks = ''
    while len(number_of_tracks)==0 or not number_of_tracks.isdecimal():
        print('1層あたり撮影するトラック数を入力してください')
        number_of_tracks = input()
    number_of_tracks = int(number_of_tracks)

    # 配列の初期化
    temperature_time = np.array([])
    temperature_track = np.array([])
    temperature_layer = np.array([])
    z_pitch_time = np.array([])
    z_pitch_track = np.array([])
    z_pitch_layer = np.array([])

    client = Client('opc.tcp://169.254.1.15:4840/')
    try:
        client.connect()
        R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
        v0 = ua.Variant(0, ua.VariantType.Double)
        R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                
        while True:
            # R0の監視
            R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
            r0 = R0.get_value()
            if r0 == 0:# MPFによる指示待ち
                time.sleep(0.1)# 0.5秒単位でループ
                print('処理してないよ')

                # R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                # v0 = ua.Variant(1, ua.VariantType.Double)
                # R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                        
                continue
            elif r0 == 1:
                # 定数の初期化
                sum_y = 0
                sum_temperature = 0

                # pyautoguiによる溶融地撮影
                # time.sleep(0.5)
                for i in range(number_of_images):
                    time.sleep(0.4)
                    pyautogui.click(1034, 489)
                time.sleep(0.2)
                # imagesディレクトリ内の最後に更新された画像を取得
                images_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'temp' + os.sep + 'images' + os.sep
                file_list = sorted(glob.glob(images_dir + '*.bmp'), key=os.path.getmtime, reverse=True)
                analyze_file_list = [file_list[i] for i in range(number_of_images)]
                
                for image_path in analyze_file_list:
                    ic(image_path)
                    img = np.array(Image.open(image_path))

                    # SODの算出
                    x,y = get_gravitypoint_CMOS(img, show_gp_img = False, print_gp = False)
                    sod = (y + 15.572) / 46.283
                    z_pitch = 13 - sod
                    z_pitch_time = np.append(z_pitch_time, z_pitch)

                    # 平均温度の算出
                    trimmed_img_r = img[ y - int(height/2) : y + int(height/2) , x - int(width/2) : x + int(width/2), 0]
                    trimmed_img_g = img[ y - int(height/2) : y + int(height/2) , x - int(width/2) : x + int(width/2), 1]
                    trimmed_img_b = img[ y - int(height/2) : y + int(height/2) , x - int(width/2) : x + int(width/2), 2]
                    img_zero = np.zeros(height*width)

                    img_red = trimmed_img_r[:,:].reshape(height*width)
                    ret, img_thresh = cv2.threshold(img_red, threshold, 255, cv2.THRESH_BINARY)
                    trimmed_img_r = trimmed_img_r.reshape(height*width)
                    trimmed_img_g = trimmed_img_g.reshape(height*width)
                    trimmed_img_b = trimmed_img_b.reshape(height*width)
                    for i in img_thresh.nonzero()[0]:
                        img_zero[i] = trimmed_img_r[i]*coefs[0] + trimmed_img_g[i]*coefs[1] + trimmed_img_b[i]*coefs[2] + coefs[3]
                    temperature = np.sum(img_zero)/img_thresh.nonzero()[0].size
                    temperature_time = np.append(temperature_time, temperature)
                # 1トラックあたりの平均zpitchを算出
                z_pitch_track = np.append(z_pitch_track, (np.sum(z_pitch_time[-1*number_of_images:-1])+z_pitch_time[-1]) / number_of_images)
                # 1トラックあたりの平均温度算出
                temperature_track = np.append(temperature_track, (np.sum(temperature_time[-1*number_of_images:-1])+temperature_time[-1]) / number_of_images)
                R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                v0 = ua.Variant(0, ua.VariantType.Double)
                R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
            elif r0 == 2:
                # 1層あたりの平均SODを算出
                z_pitch = (np.sum(z_pitch_track[-1*number_of_tracks:-1])+z_pitch_track[-1]) / number_of_tracks
                z_pitch_layer = np.append(z_pitch_layer, z_pitch)
                ic(z_pitch)
                if z_pitch < -5 or z_pitch > 5:
                    R1 = client.get_node('ns=2;s=/Channel/Parameter/R[1]')
                    v1 = ua.Variant(0.7, ua.VariantType.Double)
                    R1.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v1))
                else:
                    # CELOSのR1に積層ピッチを書き込む
                    R1 = client.get_node('ns=2;s=/Channel/Parameter/R[1]')
                    v1 = ua.Variant(z_pitch, ua.VariantType.Double)
                    R1.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v1))
                
                # 1層あたりの平均温度算出
                temperature = (np.sum(temperature_track[-1*number_of_tracks:-1])+temperature_track[-1]) / number_of_tracks
                temperature_layer = np.append(temperature_layer, temperature)
                ic(temperature)
                # TODO: 平均温度をcsvファイルとかに記録する（なんならリアルタイムで描画したい）
                # TODO: 平均温度を元に次の層のレーザ出力を算出
                # TODO: 算出したレーザ出力をCELOSのR2に書き込む

                R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                v0 = ua.Variant(0, ua.VariantType.Double)
                R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                continue
            elif r0 == 3:
                # csvデータとして保存
                data = np.vstack([temperature_time]).T
                dt_now = datetime.datetime.now()
                nowstr = dt_now.strftime('%Y%m%d%H%M%S')
                csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'csv' + os.sep
                os.makedirs(csv_dir, exist_ok=True)
                np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
                header = ["temperature_time"]
                with open(csv_dir + nowstr + 'temperature_time.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    with open(csv_dir + 'temp.csv') as fr:
                        reader = csv.reader(fr)
                        writer.writerows(reader)
                # csvデータとして保存
                data = np.vstack([temperature_track]).T
                dt_now = datetime.datetime.now()
                nowstr = dt_now.strftime('%Y%m%d%H%M%S')
                csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'csv' + os.sep
                os.makedirs(csv_dir, exist_ok=True)
                np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
                header = ["temperature_track"]
                with open(csv_dir + nowstr + 'temperature_track.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    with open(csv_dir + 'temp.csv') as fr:
                        reader = csv.reader(fr)
                        writer.writerows(reader)
                # csvデータとして保存
                data = np.vstack([temperature_layer]).T
                dt_now = datetime.datetime.now()
                nowstr = dt_now.strftime('%Y%m%d%H%M%S')
                csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'csv' + os.sep
                os.makedirs(csv_dir, exist_ok=True)
                np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
                header = ["temperature_layer"]
                with open(csv_dir + nowstr + 'temperature_layer.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    with open(csv_dir + 'temp.csv') as fr:
                        reader = csv.reader(fr)
                        writer.writerows(reader)
                # csvデータとして保存
                data = np.vstack([z_pitch_layer]).T
                dt_now = datetime.datetime.now()
                nowstr = dt_now.strftime('%Y%m%d%H%M%S')
                csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'csv' + os.sep
                os.makedirs(csv_dir, exist_ok=True)
                np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
                header = ["z_pitch_layer"]
                with open(csv_dir + nowstr + 'z_pitch_layer.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    with open(csv_dir + 'temp.csv') as fr:
                        reader = csv.reader(fr)
                        writer.writerows(reader)
                break
        print('処理を終了しました')
        
    finally:
        client.disconnect()