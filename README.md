# doubanFmSpeackerPi
&emsp;&emsp;for doubanFmPi demo  &amp;&amp;  for xiao_C ( FmSpeakerPi -> SpeakerPi -> xiaoC -> Running xiaoC(+Lego Technic; like [this]( https://www.mi.com/toyblock/))); in the future, u can share robot like share bike/battery?

### Introduce
&emsp;&emsp;douban-FM.PI 主要是平时工作编码，休息的时候，经常听豆瓣电台的音乐；平时也关注人工智能相关的技术；加上现在人工智能-语音识别(包括唤醒)/合成技术逐渐成熟， 相关的平台服务相继开放给第三方开发者使用,对应电台的智能设备也越来越多; 加上树莓派刚出3的时候买了一个，当时只是把系统装了,了解下新功能；在网上找了下豆瓣电台好像没有对应的智能设备，于是乎自己尝试着整一个，学习下相关智能领域的知识，DIY一个桌面级的东东；买了一些外设(话筒，speaker(蓝牙播放器),LED,摄像头，Servo Motor,如果外带需要一个移动电源),还有一个TJBot的外壳，然后结合语音领域的云端服务api，以及豆瓣电台的api，豆瓣电台的api服务没有开放，需要抓包查看；既然软硬件都兼备了，just do it~！  
&emsp;&emsp;如果按照歌曲大概的结构来分的话(前奏 - 主歌 - Pre-Chorus - 副歌 - 间奏 - 主歌 - 副歌 - 桥段 - 副歌 - 结尾)；以上是前奏，副歌是做一个doubanFM一样的功能；主旋律是(ˇˍˇ)做一个小智能机器人(小C/weedge)。    
<div align="center">`听说听一个人的歌单，可以了解这个人的性格`</div>
<div align="center"><img src="http://wx3.sinaimg.cn/large/646bc66fgy1fjka0pfgbfj20ku0rs0xa.jpg" width="70%" height="70%"></div>
<div align="center"><img src="http://wx3.sinaimg.cn/large/646bc66fgy1fjka6epgtcj20ku0fmjud.jpg" width="70%" height="70%"></div>
<div align="center"><img src="http://wx4.sinaimg.cn/large/646bc66fly1fjztskocpxj208w06ogls.jpg" width="70%" height="70%"></div>

### Thinking (mind mapping)
- 人机交互(Server): 架构合理设计(骨架)，组件性能优化(器官)，业务逻辑抽象(肉体)，策略方案得当(思维)，数据深度挖掘(血液)，通俗易懂的api(颜值要高,(HAL)[http://stateless.co/hal_specification.html] /REST(Swagger)/graphQL,schema校验((Json-Schema)[http://json-schema.org/])，高效信息沟通(IPC,RPC,消息队列,消息格式/协议可扩展)，物质基础牢靠(IDC,VPC,资源管理,资源调度,作业调度)，服务实时监控修复(monit,supervisor,metrics) 
- 人机交互(Client): 交互简单，易用，便捷，高效；解决日常生活(吃穿住行,娱乐,监控)之琐碎，"懒"出新高度
- KISS: 抓本质，注细节，易封装使用
<div align="center"><img src="http://wx4.sinaimg.cn/large/646bc66fgy1fjkoihzpyfj21e70qa43q.jpg" width="100%" height="100%"></div>  
<div align="center"><img src="https://raw.githubusercontent.com/weedge/doubanFmSpeackerPi/master/design.jpg" width="100%" height="100%"></div>  

### 硬件
- usb mini话筒 * 1
- 蓝牙speaker * 1
- hmdi转接线 * 1（这个看自己情况而定，主要是想后期使用显示器做一面魔镜）
- 网线 * 1 (不是必须的，可以通过无线wifi来连接，这里主要是为了保险wifi不能用的情况，可以手机用4G/5G当个热点,pi和电脑之间的中转)
- TJbot 3D模型 * 1 (这个模型是采用TJbot已经设计好的3D模型，然后通过3D打印机打印出来，这里头可选材料很多，各种材料价格不一，选用普通的PLA材料打印也花了300+大洋；有纸质的平面设计，但是找不到打印的地方。以后可以在这个模型的基础上进行改进,DIY。也许AR技术发展起来了，但愿3D打印的成本会降低点吧)
- LED * 3x2 (分别是没电阻的和有电阻的三原色RGB控制，多买了是为了防备使用中led灯调试坏了的情况发生)
- 摄像头 * 1
- Servo Motor * 5 (暂用一个，考虑四肢的情况)
- 母对公，母对母，公对公彩排线10 * 2x3 （暂时只用前两者）
- 树莓pi * 1 (包括散热片，保护壳)
- 16G microSD卡(读卡器) * 1 (16G已经足够了，当然土豪们可以追求更大空间)  
- 移动充电电源 * 1  
整体费用大概在1000+左右~ 发烧了。

### 软件
1. jasper-client （用python写的语音交互(client)系统，采用单进程的方式管理插件，不能满足多指令同时交互)
2. TJbot （用node.js写的语音交互client系统，从外观设计到调用的语音服务api，整套服务都有(waston)。后续可能用nodejs重新写一个版本，主要是用[asyncawait](https://github.com/yortus/asyncawait)这个模块来实现事件的异步处理,python需要3.4+才能用asyncio库)
3. pi的操作系统raspbian/NOOBS
4. xiaoc（client) (用Python写的client交互系统，采用引导进程来管理多个插件子进程，通过管道通信)
5. opencv （图像视频处理使用的库，提供训练级联分类器）
6. baidu-ai (调用ai提供的服务)
7. snow-boy (在线训练语音唤醒词，或者调用接口初始化训练)
9. pocketsphix （开源语音识别工具，主要用于学习语音识别技术原理)

### Install
> 硬件设置

1. 首先需要了解下GPIO的结构,通过`gpio readall`命令查看对应开发版上的pin和BCM，如图所示:

<div align="center"><img src="http://wx1.sinaimg.cn/large/646bc66fgy1fkj1i3p828j20ry0gok62.jpg" width="70%" height="70%"></div>

2. LED,Servo,USB Microphone的接入方式如下图所示：

<div align="center"><img src="http://wx3.sinaimg.cn/large/646bc66fly1fkj0xb2ta7j212w0yakjl.jpg" width="70%" height="70%"></div>

3. [摄像头安装](https://linux.cn/article-3650-1.html)

4. 从[这里](https://ibmtjbot.github.io/#gettj)下载TJBot的3D模型,当然如果你懂3DMax,学过工业设计,自己也可以diy一个机器人外壳；3D打印可以直接通过网上找商家打印。

> 软件安装

1. 烧录一个最新的[raspbian系统](https://downloads.raspberrypi.org/raspbian_latest)镜像到SD卡中（[操作](https://www.raspberrypi.org/documentation/installation/installing-images/)）

2. 如果有hmdi连接显示器，有网线连接路由器(`arp -a`查看pi分配的ip)，2016-11-25号release的一个raspbian系统默认是不开启ssh服务的，所以需要在烧录好的boot中touch一个ssh文件，然后插入sd卡，启动就可以通过ssh连接就ok了；  

如果不需要显示器和网线，直接在系统安装设置好wifi配置，具体操作参考这篇[文章](http://blog.lxx1.com/2525)；

编辑 /etc/wpa_supplicant/wpa_supplicant.conf 文件，在末尾追加wifi配置；
```
#WPA/WPA2加密方式：
network={
	ssid="你的无线网络名称"
	psk="你的wifi密码"
	key_mgmt=WPA-PSK
}

#WEP加密方式：
network={
	ssid="你的无线网络名称（ssid）"	
	wep_key0="你的wifi密码"
	key_mgmt=NONE
}
```
   
还有一种比较hack的方法，直接操作烧录好的系统文件，一般linux系统用的是ext系列的文件系统，可以通过Paragon extfs软件来加载ext文件系统，从而直接编辑系统文件配置(etc文件夹中的相关配置文件，配置说明用man来查看具体含义吧,比如man services查看/etc/services配置说明)，然后进行初始化安装启动了。通过这种方式可以进行定制化，后续组一个[pi cluster in k8s](http://blog.kubernetes.io/2015/11/creating-a-Raspberry-Pi-cluster-running-Kubernetes-the-shopping-list-Part-1.html))

3. 更新pi的源的时候需要把/etc/apt/sources.list和/etc/apt/sources.list.d/raspi.list文件这两个文件同时更新了：(notice:这里是以jessie版本为例,`lsb_release -a`查看发布的系统信息版本)
```
/etc/apt/sources.list
deb http://mirrors.tuna.tsinghua.edu.cn/raspbian/raspbian/ jessie main non-free contrib rpi
deb-src http://mirrors.tuna.tsinghua.edu.cn/raspbian/raspbian/ jessie main non-free contrib rpi

/etc/apt/sources.list.d/raspi.list
deb http://mirrors.tuna.tsinghua.edu.cn/debian/ jessie main ui
deb-src http://mirrors.tuna.tsinghua.edu.cn/debian/ jessie main ui
```

如果update的过程中会出现:`GPG 错误：http://mirrors.tuna.tsinghua.edu.cn jessie Release: 由于没有公钥，无法验证下列签名： NO_PUBKEY 8B48AD6246925553 NO_PUBKEY 7638D0442B90D010 NO_PUBKEY CBF8D6FD518E17E1`,通过如下命令解决(KEY为对应的pubkey)：
```
sudo apt install dirmngr
gpg --keyserver pgpkeys.mit.edu --recv-key KEY
gpg -a --export KEY | sudo apt-key add -
```
然后更新软件索引清单`sudo apt-get update -o Debug::Acquire::http=true debug`(这里debug打印出获取清单静态资源的响应信息)和比较索引清单更新依赖关系`sudo apt-get upgrade -y`，更新的时间可能比较长点；

最后通过`sudo raspi-config`来设置vnc服务启用(用来通过手机，vnc客户端连接可视化操作，如果桌面系统),修改密码，hostname,时区等；对系统进行[汉化处理](https://app.yinxiang.com/shard/s2/nl/452668/801abbe5-f9b3-4c8a-acc3-ecebe0fc311d/)

4. [设置蓝牙](https://www.raspberrypi.org/magpi/bluetooth-audio-raspberry-pi-3/)

5. [安装opencv](https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/),安装过程比较久，如果不想使用图像处理的插件(使用cv2库),可以不用安装，待需要时在安装。

6. 获取代码`cd ~ && git clone https://github.com/weedge/doubanFmSpeackerPi.git xiaoc`，通过pip安装对应lib包`cd xiaoc/lib && sudo pip install -r requirements.txt`

7. 常见依赖命令和包升级：
```
出现ImportError: cannot import name DependencyWarning的情况，重新安装pip:
sudo apt-get remove python-pip
sudo easy_install pip

出现ImportError: libf77blas.so.3: cannot open shared object file: No such file or directory的情况，需要安装依赖：
sudo apt-get install libatlas-base-dev
sudo usermod -a -G audio pi (添加audio组用户)

出现：ImportError: No module named pyaudio:
sudo apt-get install python-pyaudio

pi 默认是没有sox,play命令，需要安装：
sudo apt-get install sox
#支持MP3格式文件
sudo apt-get install libsox-fmt-mp3

python 的lib包通过upgrade更新,比如numpy这个常用的数学矩阵库:
sudo pip install --upgrade numpy
```

> 修改配置
- baidu.yml-dist (百度ai api服务配置)
- bootstrap.yml-dist (引导配置)
- douban.yml-dist（豆瓣插件配置）
- feed.yml-dist（播报咨询feed(rss)插件配置,包括机器之心,今日头条新闻...etc）
- gpio.yml-dist（GPIO配置，LED和Servo）
- log.yml-dist （日志级别配置）
- mail.yml-dist (邮件服务配置)
- monitor.yml-dist（监控插件配置）
- snowboy.yml-dist (唤醒词配置)  
将以上文件配置好后，修改成.yml的后缀。

安装vim，然后安装vim IDE 进行编辑：
```
sudo apt-get install vim
git clone git://github.com/tlhunter/vimrc.git .vim
ln ~/.vim/vimrc ~/.vimrc 
```

> 添加开机启动(后续加入init.d里头，以服务的方式启动)
```
robot_dir="/home/pi/xiaoc"
bluetooth_mac=""
run=`ps -ef | grep "sh ${robot_dir}/run.sh" | grep -v grep`
if [ x"$run" = x ];then
  date=`date '+%Y%m%d%H%M%S'`
  mv ${robot_dir}/log/robot.log ${robot_dir}/log/robot.${date}.log
  nohup sh ${robot_dir}/run.sh ${bluetooth_mac} > ${robot_dir}/log/robot.log 2>&1 &
  find ${robot_dir}/log/ -type f -name "robot.*.log" -ctime +3 | xargs rm -f
  #rm_date=`date -d '2 days ago' +%Y%m%d`
  #rm -f ${robot_dir}/log/robot.${rm_date}*.log
fi
```
将以上代码追加至~/.bashrc中，添加已经匹配信任好了的蓝牙MAC地址， 然后重启

### plugin
&emsp;&emsp;插件开发(后续的设计完善参考es插件(比如IK分词(感叹一下，在工程中经常用到的小插件关注度往往比小众软件系统要高的多，这也和对应的生态有关系，所以选择很重要？喜欢就好吧！))的管理，其实思路一样(工程上的实现方式有些差异))，因为需要插件进程和父进程(bootstrap进程)通过管道通信，分为两种情况：
- 1.插件进程运行不需要轮训，运行完就可以结束，开发可参考[音量控制插件](https://github.com/weedge/doubanFmSpeackerPi/tree/master/plugin/volume)；
- 2.插件进程启动后不退出，轮训接受消息，需要结束消息/信号结束插件进程，开发可参考[新闻播报插件](https://github.com/weedge/doubanFmSpeackerPi/tree/master/plugin/feeds)。

&emsp;&emsp;如果改成插件线程，可参考PHP中线程安全([ZTS](http://blog.codinglabs.org/articles/zend-thread-safety.html),想法借鉴就行了，至于它的实现。。。并发设计可以参考java中的java.util.concurrent并发框架包的实现)的设计想法；  系统底层通过两种机制来保证原子操作：总线锁，缓存锁；处理器提供了很多lock前缀的指令来实现，比如交换指令XADD,CMPXCHG,ADD,OR和其他一些操作数和逻辑指令，被这些指令操作的内存区域就会加锁，导致其他处理器不能同时访问它；一个简单内核系统sanos的原子操作[atomic.h](http://www.jbox.dk/sanos/source/include/atomic.h.html)；  通过自旋锁(spin_lock)和互斥锁(mutex_lock)的比较，来选择适合的场景:  
- [临界区执行时间短的情况：队列消费操作](https://gist.github.com/weedge/3f94e9c6144e6b3d11fa55f6801d0e1b)  
- [临界区执行时间长的情况](https://gist.github.com/weedge/01d1a9934cbc61726793b80d044ce6ed)

- [x] doubanfm: 播放豆瓣电台,下一首,暂停,继续播放, 喜欢这首歌, 不喜欢这首歌, 删除这首歌, 不再播放这首歌, 不在播放这首歌, 播放到我的私人频道,切换到我的私人频道, 我的私人频道, 私人频道, 播放红心歌单, 切换到红心电台, 切换到红心歌单, 红心歌单, 红心电台, 播放红星歌单, 切换到红星电台, 切换到红星歌单, 红星歌单, 红星电台,下载, 下载这首歌,关闭豆瓣电台,结束豆瓣电台
- [x] 音量控制: 安静,声音大一点,声音再小一点,打开声音,声音小一点,声音小点,声音在小一点,声音大点,静音,声音在大一点,声音再大一点 
- [x] 新闻播报：阅读机器之心新闻，阅读下一条,下一条,更新新闻,关闭阅读,结束阅读
- [x] 人体监控：开始人体监控，打开人体监控，结束人体监控，关闭人体监控 （如果加上其他类型监控，需要采用多线程对camera共享资源做操作）
- [x] 声控拍照/视频：这是什么菜品，这是什么车，这是什么植物，这是什么动物，这是什么标志  
(物体识别，场景适合幼儿园的小朋友；视频的话可以做一个监控，通过实时监控的视频数据包(packet),或者是每一帧的图片数据(frame)，通过管道的形式发到莫个服务端口，这个端口可以是本地监听的端口，比如用http协议访问这个端口就可以了(用VLC/mjpg-streamer软件可以实现视频数据包的形式，也可以用opencv直接获取每一帧的图片数据)，虽然是实时的，但是对于pi来说这种比较耗资源；还有种是方式是将视频数据包发送到中转服务端口上，然后通过中转服务将视频报转发给视频直播的云服务接口，中转服务可以做一层过滤发现，简单的处理方式是通过netcat(nc)将数据包转发到中转服务端口上，通过中转服务做进一步处理(放入buffer里头，定点上传等)，中转服务访问量不大的情况下，可以直接用nc来取数据，不需要考虑事件机制(如果需要的话可以用c++来实现一个简单的接受视频数据包服务，利用epoll注册监听/接受/读/写事件))。  
简单实现：  
&emsp;&emsp;Client in PI [photographToClientSocket.py](https://gist.github.com/weedge/199010c48201ea9efe5c0e350ef5d02d),[videoToClientSocket.py](https://gist.github.com/weedge/86c356f1000fa03cc69edb905bd51dcb);  
&emsp;&emsp;Server in my Mac [photographToServerSocket.py](https://gist.github.com/weedge/f87e84805b1e646514e17c2a6b1c8978), [videoToPlayerFromServerSocket.py](https://gist.github.com/weedge/ee9c99baffac998123cb27ea083dec0c).

***参考链接***
1. [init系统介绍](https://www.ibm.com/developerworks/cn/linux/1407_liuming_init1/index.html)
2. [snowboy](http://docs.kitt.ai/snowboy/)
3. [tjbot](https://github.com/ibmtjbot/tjbot)
4. [jasper-client](https://jasperproject.github.io/documentation/)
5. [pocketsphix](https://cmusphinx.github.io/wiki/tutorialpocketsphinx/)
6. [rpc框架](https://www.zhihu.com/question/25536695)(回答中提到[责任链框架](https://docs.jboss.org/netty/3.2/api/org/jboss/netty/channel/ChannelPipeline.html)在实际的工作写业务代码框架也用到，有点类似[AOP](https://www.zhihu.com/question/24863332) addBefore,addAfter... [简单示例](https://github.com/weedge/myframe/blob/master/src/libs/AppController.php))
7. [BerkeleDB简介](https://www.ibm.com/developerworks/cn/linux/l-embdb/index.html)，[reference](http://docs.oracle.com/cd/E17076_02/html/programmer_reference/index.html)，[capi](http://docs.oracle.com/cd/E17076_02/html/api_reference/C/frame_main.html)
8. [蓝牙编程](http://people.csail.mit.edu/albert/bluez-intro/c212.html)([PyBluez](https://github.com/karulis/pybluez))
9. [语音识别的技术原理-知乎回答](https://www.zhihu.com/question/20398418)
10. [在pi上运行TensorFlow](https://github.com/samjabrahams/tensorflow-on-raspberry-pi)
11. [XNOR-Net: ImageNet Classification Using Binary Convolutional Neural Networks](http://allenai.org/plato/xnornet/)(采用torch框架)
12. [pi+Python + OpenCV监控](https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/)、 [Smart Security Camera](https://www.hackster.io/hackerhouse/smart-security-camera-90d7bd)
13. [opencv3.3.0开发文档](http://docs.opencv.org/3.3.0/)

### 声明
现定义为桌面级产品(对于机器学习中的算法模型，可以作为验证已训练好模型的client工具环境)，代码请勿用于商业用途，如果有需要请联系作者(weege007#gmail)
### License
This project uses the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0) software license.

### [todo](https://github.com/weedge/doubanFmSpeackerPi/blob/master/TODO.md)
