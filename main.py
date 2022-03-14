# ESP8266板子：WeMos.cc D1 mini V3.0
################################################
#           接线图
# PN532                  ESP8266
# SCL-------------------D7(GPIO13)
# SDA-------------------D2(GPIO4)
# GND-------------------GND
# VCC---D极(MOS管)S极--- VCC
#             G极
#              |
#              ----------D3(GPIO0)
#
# 
# 车钥匙                   ESP8266
# 上锁----(+ 二极管 -)----D5(GPIO14)
# 解锁----(+ 二极管 -)----D6(GPIO12)
# VCC--------------------D1(GPIO5)
# GND--------------------GND
#
#
# PMOS管（AOD409）：大脚接PN532负极，左下接控制(GPIO0)，右下接GND
# 车钥匙按键是低电平触发
######################################################
# 更新日志：
# v0.2
# 由原来的连续检测卡片改为间隔380ms检测一次卡片，如检测不到卡片，则进行休眠并关闭RF射频场以省电。
# v0.3
# 取消卡号不正确的暂停2秒，检测卡片间隔改为280ms，取消判断密钥验证步骤，卡移开暂停时间改为1秒,降低初始化时间到1秒，
# 意外累计次数改为20次,取消10扇区密钥校验,检测不到卡片清零异常状况次数。
# v0.3
# i2c初始化放到nfc通电以后，同时nfc通电前拉低scl和sda的电平
# V0.4
# 电路更换NMOS管为PMOS管（AOD409低电平导通）
# 添加上锁次数记录，每上锁14次重启设备

from machine import Pin, I2C, reset
import time
import binascii
import network
station = network.WLAN(network.AP_IF)
station.active(False)
#binascii.hexlify()
#返回的16进制字节用.decode()转换成字符串。

def hextobyte(info):
    return bytearray([int(x,16) for x in info.split(" ")])

def readnfc(x):
    global count_exp
    try:
        t2 = time.ticks_ms()
        r = i2c.readfrom(36,x)
    except:
        count_exp += 1
        r = None
    return r

def writenfc(info):
    global count_exp
    try:
        i2c.writeto(36,info)
    except:
        count_exp += 1
    
#读取车辆状态，0表示已上锁，1表示已解锁
def read_status():
    with open("status.txt","r") as f:
        r = f.read()
        if int(r):
            return True
        if not int(r):
            return False

#更新车辆状态
def update_status(i):
    with open("status.txt","w") as f:
        if i:
            f.write("1")
        if not i:
            f.write("0")
            
#关闭RF射频场一段时间进行省电。
def nfc_powerdown(t):
    writenfc(send_powerdown)
    readnfc(7)
    time.sleep_ms(15)
    readnfc(20)
    time.sleep_ms(t)
    

car_unlock_led = Pin(2,Pin.OUT)#8266板载LED，低电平点亮
car_unlock = Pin(12,Pin.OUT)#解锁控制,上升沿触发
car_lock = Pin(14,Pin.OUT)#上锁控制，上升沿触发
car_vcc = Pin(5,Pin.OUT)#钥匙供电
nfc_power_ctrl = Pin(0,Pin.OUT)#nfc模块供电控制(接MOS管),
card_leave = True#刷卡后卡是否离开状态标志。防止重复执行解锁和上锁。
count_exp = 0#异常状况次数记录，超过阈值重启8266
send_wakeup = hextobyte("55 55 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FF 03 FD D4 14 01 17 00")
send_read_uid = hextobyte("00 00 FF 04 FC D4 4A 01 00 E1 00")
recv_uid = b'\x01\x00\x00\xff\x0c\xf4\xd5K\x01\x01\x00\x04\x08\x04*****请将这里改为自己的卡ID*****\x00'
recv_no_uid = b'\x00\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'
send_check_pass2 = hextobyte("00 00 FF 0F F1 D4 40 01 60 0B *****请将这里改为自己的对应扇区密钥A + 卡ID***** A6 00")
recv_check_pass2 = b'\x01\x00\x00\xff\x03\xfd\xd5A\x00\xea\x00'
send_read_data2 = hextobyte("00 00 FF 05 FB D4 40 01 30 08 B3 00")
recv_read_data2 = b'\x01\x00\x00\xff\x13\xed\xd5A\x00*****请将这里改为自己卡对应块的数据*****\x00'
send_check_pass10 = hextobyte("00 00 FF 0F F1 D4 40 01 60 2B *****请将这里改为自己卡对应扇区密钥A + 卡ID***** AF 00")
recv_check_pass10 = b'\x01\x00\x00\xff\x03\xfd\xd5A\x00\xea\x00'
send_read_data10 = hextobyte("00 00 FF 05 FB D4 40 01 30 28 93 00")
recv_read_data10 = b'\x01\x00\x00\xff\x13\xed\xd5A\x00*****请将这里改为自己卡对应块的数据*****\x00'
send_powerdown = hextobyte("00 00 FF 03 FD D4 16 80 96 00")
pn532_response = b'\x01\x00\x00\xff\x00\xff\x00'
pn532_disconnect = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

#初始化，
#各控制电平复位
car_unlock_led.on()
car_unlock.on()
car_lock.on()
car_vcc.off()
#读取上次存储的车辆状态
car_status = read_status()
if car_status:
    car_vcc.on()
    car_unlock_led.off()
#重启NFC模块,scl、sda、vcc线拉低电平
nfc_power_ctrl.on()
Pin(13,Pin.OUT).off()
Pin(4,Pin.OUT).off()
time.sleep_ms(500)
nfc_power_ctrl.off()
i2c = I2C(scl=Pin(13), sda=Pin(4), freq=100000)
time.sleep_ms(300)
#初始化完毕


#把主循环代码写到try里面，出现意外情况自动重启8266
try:
    lock_times = 0#上锁计次，
    while count_exp < 20 and lock_times < 14:
        #唤醒
        writenfc(send_wakeup)
        time.sleep_ms(5)
        readnfc(7)
        time.sleep_ms(15)
        readnfc(10)
        #读卡UID号
        writenfc(send_read_uid)
        readnfc(7)
        time.sleep_ms(25)
        uid = readnfc(20)
        #print("uid",uid)
        if uid == recv_no_uid:
            #读取不到卡片
            count_exp = 0
            nfc_powerdown(280)
            continue
        elif uid == recv_uid:
            #检测到正确uid
            writenfc(send_check_pass2)
            #验证2扇区密钥A
            readnfc(7)
            time.sleep_ms(20)
            readnfc(11)
            writenfc(send_read_data2)
            #读取对应块数据
            readnfc(7)
            time.sleep_ms(25)
            if readnfc(27) == recv_read_data2:
                if car_status:#如果车是解锁状态，需要对其上锁,
                    car_lock.off()#按下
                    time.sleep_ms(30)
                    car_lock.on()#抬起
                    time.sleep_ms(500)
                    #车钥匙按键是上升沿触发，需要等待触发完毕(预留500ms)才能关闭钥匙电源
                    car_vcc.off()
                    car_unlock_led.on()
                    update_status(False)
                    car_status = not car_status
                    #print("上锁成功")
                    lock_times += 1
                else:
                    car_vcc.on()
                    time.sleep_ms(300)
                    car_unlock.off()
                    car_unlock_led.off()
                    time.sleep_ms(30)
                    car_unlock.on()
                    update_status(True)
                    car_status = not car_status
                    #print("解锁成功")
            while True:#不论卡片信息验证是否通过，都检测卡片是否拿开,避免重复触发。
                writenfc(send_read_uid)
                readnfc(7)
                time.sleep_ms(30)
                if readnfc(20) != recv_uid:
                    nfc_powerdown(1000)
                    break
        elif uid == pn532_disconnect:#pn532与主机断开连接
            count_exp += 1
            nfc_powerdown(1000)
        else:#如果以上都不通过，说明卡uid不正确，停留较长时间再检测，防止有人恶意破解
            nfc_powerdown(2800)

except:
   pass
reset()#出现意外情况或者读写错误超出阈值后重启8266

