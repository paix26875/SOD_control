from opcua import Client, ua

client=Client("opc.tcp://169.254.1.15:4840/")

if __name__ == '__main__':
    try:
      client.connect()
      
      while True:
          R5 = client.get_node('ns=2;s=/Channel/Parameter/R[5]')
          r5 = R5.get_value()
          if r5 == 0:
            methodNode = client.get_node("ns=2;s=/Methods")
            readVar = ua.QualifiedName("/Methods/ReadVar",2) # 値を読み出す関数名、引数の2は上のns=?と同じ値。
            machineCoordinate = methodNode.call_method(readVar,"/Channel/GeometricAxis/actToolBasePos[u1,1,3]" )# 機械座標の1～3軸を取得
            workCoordinate = methodNode.call_method(readVar, "/Channel/GeometricAxis/actToolEdgeCenterPos[u1,1,3]") # ワーク座標の1～3軸を取得
            print("Machine Coordinate: " + machineCoordinate)
            print("Work Coordinate: " + workCoordinate)
          # r1 = methodNode.call_method(readVar, "/Channel/Parameter/R[u1, 1]") # R100の値を取得。
          # print("R1: " + r1) # R100の値を表示。
          # writeVar = ua.QualifiedName("/Methods/WriteVar", 2) # 値を書き込む関数名。
          # methodNode.call_method(writeVar, "/Channel/Parameter/R[u1, 100]", 10)
            continue
          elif r5 == 1:
            break

    finally:
      client.disconnect()