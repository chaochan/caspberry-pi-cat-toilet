# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import subprocess


# 猫感センサーの入力を監視するGPIO番号
GPIO_NO_CAT_SENSOR = 27     # 13番ピン
# テスト用LED出力GPIO番号
GPIO_NO_LED = 17            # 11番ピン

# ポーリング時のスリープ時間(秒)
POLLING_SLEEP_TIME_SEC = 1

# センサー反応後のスリープ時間(反応するたびLINE通知するのを防ぐため)
CAT_SENSOR_ENABLED_SLEEP_TIME_SEC = 3 * 60
# センサー反応時のLINE通知メッセージ
CAT_SENSOR_ENABLED_LINE_MESSAGE = 'トイレに入ったよ😺'

# LINE通知のURL
LINE_NOTIFY_URL = 'https://notify-api.line.me/api/notify'

# 設定ファイルのロード(ここでアクセストークン等の見えない情報を設定させる)
try:
    from settings import *
except ImportError:
    DEBUG = True
    LINE_TOKEN = None   # これは settings.py 側で設定されるべき
    pass


def line_notify(message, token):
    # LINEへ送信
    command = "curl -X POST -H 'Authorization: Bearer {0}' -F 'message={1}' {2}".format(token, message, LINE_NOTIFY_URL)
    subprocess.getoutput(command)


def main():
    GPIO.cleanup()

    # GPIO番号で指定
    GPIO.setmode(GPIO.BCM)
    # 猫感センサーは入力
    GPIO.setup(GPIO_NO_CAT_SENSOR, GPIO.IN)
    if DEBUG:
        GPIO.setup(GPIO_NO_LED, GPIO.OUT)

    # ポーリング監視
    counter = 0
    enabled_cat_sensor = False
    while True:
        # 猫感センサー反応してる？
        enabled_cat_sensor_before = enabled_cat_sensor
        enabled_cat_sensor = (GPIO.input(GPIO_NO_CAT_SENSOR) == GPIO.HIGH)

        if counter > 0:
            counter += 1
        if counter >= 10:
            counter = 0

        # 前回までセンサが反応している場合はカウント開始
        # 指定カウント以内で再度センサ反応していれば、トイレに入っている事にする
        if enabled_cat_sensor_before and not enabled_cat_sensor:
            counter += 1

        if DEBUG:
            print(enabled_cat_sensor)
            # デバッグ時はLED点灯/消灯
            GPIO.output(GPIO_NO_LED, GPIO.HIGH if enabled_cat_sensor else GPIO.LOW)
        else:
            if enabled_cat_sensor:
                if counter > 0:
                    line_notify(message=CAT_SENSOR_ENABLED_LINE_MESSAGE, token=LINE_TOKEN)
                    time.sleep(CAT_SENSOR_ENABLED_SLEEP_TIME_SEC)   # LINE通知後はしばらくスリープ(何回も通知されるのを防ぐため)
                    counter = 0

        time.sleep(POLLING_SLEEP_TIME_SEC)


if __name__ == "__main__":
    main()
