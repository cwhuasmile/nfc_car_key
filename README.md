# nfc_car_key

场景复现：车钥匙又大又重，装口袋太占地方，能不能把他做成卡片式的，类似现在的新能源车一样，，，等等，人家不都是能用手机解锁汽车的么?说的也是，我为什么不自己做一个呢，这样出门只需要带一个手机就行了。

成功后的总结先写到前面，为了劝退很多人。该方案需要满足的条件1：汽车带无钥匙进入和一键启动功能，2：需要永久性的放一把钥匙再车内。

做这个项目需要掌握四方面的知识，1-python，2-esp8266，3-nfc通信(PN532模块)，4-MifareOne IC卡通信

方案需要的材料：ESP8266模块、PN532模块、车钥匙、AOD409(P-MOS管)、二极管

原理：esp8266控制pn532循环检测IC卡的存在，读取IC卡的信息是否符合要求，触发车钥匙开关。。

难点在于PN532和IC卡的通信，数据传输、判断、校验都是以字节的形式，请仔细阅读PN532手册。

电路接线图在main.py文件内


引用连接：
https://www.cnblogs.com/zhupengfei/p/8983666.html

https://www.nxp.com/docs/en/user-guide/141520.pdf

https://4hou.win/wordpress/?cat=453

https://blog.csdn.net/shdlshmm/article/details/102930710

https://www.shangmayuan.com/a/05bd0c03345e4fadb4910900.html
