import datetime

from temp import setting

def main():
    # データを表示する
    info = setting.user_info
    print(info["name"])
    print(info["url"])

if __name__ == '__main__':
    main()
    