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

def post_log(text):
    '''
    ログ出しする関数
    yy/mm/dd hh:mm:ss ログの内容

    Parameters
    ----------
    text : str
        ログに出力したいテキスト
    '''
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    with open('temp' + os.sep + 'log.txt', 'a') as f:
        print(now + ' ' + text, file=f)


if __name__ == '__main__':
    with open('temp/log.txt', 'a') as f:
        print('', file=f)
    post_log('Start!!!!!')
    print('Enter the reference temperature.')
    ReferenceTemperature = int(input())
    post_log('Reference temperature : ' + str(ReferenceTemperature))
    # 定数の設定
    number_of_images = 3
    height = 300
    width = 300
    threshold = 20
    resolution = 0.023 # TODO: 分解能（mm/pixel）
    frame_rate = 5 # TODO: フレームレート（fps）
    interval = 1/frame_rate # 撮影間隔（sec）
    feed_rate = 1000 #  走査速度（mm/min）
    deviation_gravitypoint = int(feed_rate / 60 * interval / resolution)#  次のフレームの重心位置からのズレ（pixel）
    # if feed_rate / 60 * interval > 1.5:
    #     ic(deviation_gravitypoint)
    #     ic(feed_rate / 60 * interval)
    #     print('フレームレートが適切に設定されていません')
    #     sys.exit()
    coefs = np.array([ 2.15489147e+00, -1.50682127e+00,  6.00025683e+00,  1.77044939e+03])#f4g16

    # 配列の初期化
    temperature_history = np.array([])
    z_pitch_history = np.array([])
    processing_time_history = np.array([])
    cooling_rate_history = np.array([])
    cooling_rates = np.array([])
    laserPower_history = np.array([])

    try:
        client = Client('opc.tcp://169.254.1.15:4840/')
        client.connect()
        R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
        v0 = ua.Variant(0, ua.VariantType.Double)
        R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                
        while True:
            # R0の監視
            R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
            r0 = R0.get_value()
            if r0 == 0:# MPFによる指示待ち
                time.sleep(0.5)# 0.5秒単位でループ
                print('処理してないよ')

                # R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                # v0 = ua.Variant(1, ua.VariantType.Double)
                # R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                        
                continue
            elif r0 == 1:
                # 定数の初期化
                sum_y = 0
                sum_temperature = 0
                lower_temperatures = np.array([])
                gp_temperatures = np.array([])

                start = time.time()

                R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                v0 = ua.Variant(2, ua.VariantType.Double)
                R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))
                # pyautoguiによる溶融地撮影
                # time.sleep(0.5)
                for i in range(number_of_images):
                    time.sleep(0.5)
                    pyautogui.click(1044, 491)

                # imagesディレクトリ内の最後に更新された画像を取得
                images_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'temp' + os.sep + 'images' + os.sep
                file_list = sorted(glob.glob(images_dir + '*.bmp'), key=os.path.getmtime, reverse=True)
                analyze_file_list = [file_list[i] for i in range(number_of_images)]
                
                for image_path in analyze_file_list:
                    ic(image_path)
                    img = np.array(Image.open(image_path))

                    # SODの算出
                    x,y = get_gravitypoint_CMOS(img, show_gp_img = False, print_gp = False)
                    sum_y += y

                    # 冷却速度算出用の温度を記録する
                    # cool_y = y - deviation_gravitypoint # 冷却速度測定用の座標
                    # lower_temperature = img[cool_y, x, 0]*coefs[0] + img[cool_y, x, 1]*coefs[1] + img[cool_y, x, 2]*coefs[2] + coefs[3]
                    # lower_temperatures = np.append(lower_temperatures, lower_temperature)
                    # gp_temperature = img[y, x, 0]*coefs[0] + img[y, x, 1]*coefs[1] + img[y, x, 2]*coefs[2] + coefs[3]
                    # gp_temperatures = np.append(gp_temperatures, gp_temperature)

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
                        temperature = trimmed_img_r[i]*coefs[0] + trimmed_img_g[i]*coefs[1] + trimmed_img_b[i]*coefs[2] + coefs[3]
                        if temperature > 1890 and temperature < 2310:
                            img_zero[i] = temperature
                        else:
                            continue
                    temperature = np.sum(img_zero)/img_zero.nonzero()[0].size
                    sum_temperature += temperature
                # 1層あたりの平均SOD，平均温度、平均冷却速度を算出する
                # for i in range(gp_temperatures.size-1):
                #     cooling_rates = np.append(cooling_rates, (gp_temperatures[i] - lower_temperatures[i+1]) / interval)
                # average_coolingrate = np.sum(cooling_rates[1-number_of_images:]) / number_of_images-1
                # cooling_rates = np.append(cooling_rates, np.zeros(number_of_images))
                # ic(average_coolingrate)
                # cooling_rate_history = np.append(cooling_rate_history, average_coolingrate)

                average_y = sum_y / number_of_images
                ic(average_y)
                sod = (average_y - 59.372) / 42.117
                z_pitch = 13 - sod
                ic(z_pitch)
                z_pitch_history = np.append(z_pitch_history, z_pitch)
                if z_pitch < -5 or z_pitch > 5:
                    R1 = client.get_node('ns=2;s=/Channel/Parameter/R[1]')
                    v1 = ua.Variant(0.4, ua.VariantType.Double)
                    R1.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v1))
                else:
                    # CELOSのR1に積層ピッチを書き込む
                    R1 = client.get_node('ns=2;s=/Channel/Parameter/R[1]')
                    v1 = ua.Variant(z_pitch, ua.VariantType.Double)
                    R1.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v1))
                
                average_temperature = sum_temperature / number_of_images
                ic(average_temperature)
                temperature_history = np.append(temperature_history, average_temperature)
                # TODO: 平均温度をcsvファイルとかに記録する（なんならリアルタイムで描画したい）
                
                # 前回のレーザ出力を取得
                R2 = client.get_node('ns=2;s=/Channel/Parameter/R[2]')
                r2 = R2.get_value()
                laserPower = r2
                # 平均温度を元に次の層のレーザ出力を算出
                if average_temperature >= ReferenceTemperature:
                    laserPower -= 20
                else:
                    laserPower += 20
                # 算出したレーザ出力をCELOSのR2に書き込む
                if laserPower > 2000:
                    laserPower_history = np.append(laserPower_history, r2)
                else:
                    R2 = client.get_node('ns=2;s=/Channel/Parameter/R[2]')
                    v2 = ua.Variant(laserPower, ua.VariantType.Double)
                    R2.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v2))
                    laserPower_history = np.append(laserPower_history, laserPower)

                R0 = client.get_node('ns=2;s=/Channel/Parameter/R[0]')
                v0 = ua.Variant(0, ua.VariantType.Double)
                R0.set_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v0))

                end = time.time()
                elapsed_time = end - start
                ic(elapsed_time)
                processing_time_history = np.append(processing_time_history, elapsed_time)
                continue
            elif r0 == 3:
                print('CELOSによるプログラム終了指示がありました。プログラムを終了しデータを保存します。')
                break
    except Exception as e:
        print('エラーが発生しました。プログラムを中断します。')
        print(e)
        post_log('Error with : ' + str(e))
    finally:
        # csvデータとして保存
        # data = np.vstack([z_pitch_history, temperature_history, cooling_rate_history, processing_time_history]).T
        data = np.vstack([z_pitch_history, temperature_history, laserPower_history, processing_time_history]).T
        dt_now = datetime.datetime.now()
        nowstr = dt_now.strftime('%Y%m%d%H%M%S')
        csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'temp' + os.sep +'csv' + os.sep
        os.makedirs(csv_dir, exist_ok=True)
        np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
        # header = ["z_pitch","temperature","cooling_rate_history","processing_time"]
        header = ["z_pitch","temperature","laserPower_history","processing_time"]
        with open(csv_dir + nowstr + '.csv', 'w', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            with open(csv_dir + 'temp.csv') as fr:
                reader = csv.reader(fr)
                writer.writerows(reader)
        # csvデータとして保存
        # time = np.arange(cooling_rates.size)
        # data = np.vstack([time, cooling_rates]).T
        # dt_now = datetime.datetime.now()
        # nowstr = dt_now.strftime('%Y%m%d%H%M%S')
        # csv_dir = os.path.dirname(os.getcwd() + os.sep + __file__) + os.sep + 'temp' + os.sep +'csv' + os.sep
        # os.makedirs(csv_dir, exist_ok=True)
        # np.savetxt(csv_dir + 'temp.csv', data, delimiter=',', fmt='%.6e')
        # header = ["time", "cooling_rate"]
        # with open(csv_dir + nowstr + 'cooling_rate_time.csv', 'w', newline="") as f:
        #     writer = csv.writer(f)
        #     writer.writerow(header)
        #     with open(csv_dir + 'temp.csv') as fr:
        #         reader = csv.reader(fr)
        #         writer.writerows(reader)
        try:
            client.disconnect()
            print('接続を切断しました')
        except Exception as e:
            print(e)
            post_log(str(e))
        print('プログラムを終了しました')
        post_log('Finish!!!')