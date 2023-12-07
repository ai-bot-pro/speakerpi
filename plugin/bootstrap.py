# -*- coding: utf-8-*-
import os
import re
import pkgutil
from multiprocessing import Process, Queue, Pipe
from lib.gpio.manager import Manager as gpioManager

import lib.appPath
import lib.util
from lib.gpio.servo import Servo
from lib.gpio.led import Led

class Bootstrap(object):

    def __init__(self, speaker, ai_chat, config):
        """
        加载插件，通过指令引导执行对应插件模块
        """
        self._logger = lib.util.init_logger(__name__)
        self.speaker = speaker
        self.ai_chat = ai_chat
        self.config = config
        self.plugins = self.get_plugins(config)

        self.son_processors = {}
        #to_pipe 父进程->子进程的pipe 输入(w)
        self.in_to_fps = {}
        #from_pipe 子进程->父进程的pipe 输出(r)
        self.out_from_fps = {}
        for plugin in self.plugins:
            pid_file = os.path.join(lib.appPath.DATA_PATH, plugin.CATE+"_"+plugin.__name__+'.pid');
            if os.path.exists(pid_file):
                os.remove(pid_file)
            #self.son_processors[plugin.TAG],self.in_to_fps[plugin.TAG],self.out_from_fps[plugin.TAG] = self.create_plugin_process(plugin,speaker)

    @classmethod
    def create_plugin_process(cls,plugin,speaker,block=False): 
        out_to_fp, in_to_fp = Pipe(True)
        out_from_fp, in_from_fp = Pipe(True)
        son_processor = Process(target=cls.son_process, args=(speaker,
            (out_to_fp, in_to_fp),
            (out_from_fp, in_from_fp),
            plugin.son_process_handle,block))

        son_processor.start()
        # 等to_pipe被fork 后，关闭主进程的输出端; 创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
        out_to_fp.close()
        # 等from_pipe被fork 后，关闭主进程的输入端; 创建的Pipe一端连接着子进程的输入，一端连接着父进程的输出口
        in_from_fp.close()

        #其实直接可以通过son_processor.pid来判断是否进程还在，写入文件主要是方便查看当前运行的插件进程
        pid_file = os.path.join(lib.appPath.DATA_PATH,plugin.CATE+"_"+plugin.__name__+".pid")
        with open(pid_file, 'w') as pid_fp:
            pid_fp.write(str(son_processor.pid))
            pid_fp.close()

        return [son_processor,in_to_fp,out_from_fp]

    @classmethod
    def son_process(cls, speaker, from_pipe, to_pipe, handle_callback=None, block=False):
        '''
        from_pipe: 相对协同进程的，用于父进程发送消息给子进程のpipe
        to_pipe: 用于子进程发送消息给父进程のpipe
        handle_callback: 为轮训获取pipe中的数据进行相应逻辑处理函数,参数为从pipe中获取通信数据的回调函数,
        speaker: voice实例(tts)
        '''
        _out_from_fp, _in_from_fp = from_pipe
        _out_to_fp, _in_to_fp = to_pipe
    
        def get_text():
            text = None
            if block==True:
                text = _out_from_fp.recv()
            else:
                if _out_from_fp.poll():
                    text = _out_from_fp.recv()
            return text

        _in_from_fp.close()
        _out_to_fp.close()
        if handle_callback is not None:
            handle_callback(speaker,_in_to_fp,_out_from_fp,get_text)

    def __del__(self):
        self._logger.debug("______ delete bootstrap ______")
        for (plugin_tags,son_processor) in self.son_processors.items():
            self.in_to_fps[plugin_tags].close()
            self.out_from_fps[plugin_tags].close()
            son_processor.join()

    @classmethod
    def get_plugins(cls,config):
        """
        通过引导配置获取插件模块，通过插件模块中的PRIORITY属性控制优先级，按大到小排序，越大越优先
        """
        plugins = []
        locations = []
        tags = []
        cates = []
        logger = lib.util.init_logger(__name__)
        if "plugins" in config:
            for (cate,plugin_tags) in config['plugins'].items():
                locations.append(os.path.join(lib.appPath.PLUGIN_PATH,cate))
                tags.extend(plugin_tags.keys())
                cates.append(cate)

        tags = list(set(tags))

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                plugin = loader.load_module(name)
            except:
                logger.warning("Skipped plugin '%s' due to an error.", name, exc_info=True)
            else:
                if ( (hasattr(plugin, 'isValid')) 
                    and (hasattr(plugin, 'process_handle')) 
                    and (hasattr(plugin, 'son_process_handle')) 
                    and (hasattr(plugin, 'TAG')) and (plugin.TAG in tags) 
                    and (hasattr(plugin, 'CATE')) and (plugin.CATE in cates) ):
                    logger.debug("Found plugin '%s' with tag: %r", name, plugin.TAG)
                    plugins.append(plugin)
                else:
                    logger.warning("Skipped plugin '%s' because it misses " + "the TAG constant.", name)

        plugins.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY') else 0, reverse=True)

        return plugins

    def query(self,texts,queue=None):
        """
        引导识别的texts给对应的插件处理
        """
        if queue is not None:
            texts = queue.get(True)

        for plugin in self.plugins:
            for text in texts:

                self._logger.debug("Started to bootstrap asr word to plunin %s with input:%s", plugin, text)
                text = lib.util.filt_punctuation(text)

                if self.config['plugins'][plugin.CATE][plugin.TAG]['begin_instruction']:
                    begin_instruction = self.config['plugins'][plugin.CATE][plugin.TAG]['begin_instruction']
                    begin_instruction = begin_instruction.split(",")
                    if (any(phrase in text for phrase in begin_instruction)
                            and self.getPluginPid(plugin) is None):
                        self._logger.debug("Create a process for plunin %s with input:%s", plugin, text)
                        self.son_processors[plugin.TAG],self.in_to_fps[plugin.TAG],self.out_from_fps[plugin.TAG] = self.create_plugin_process(plugin,self.speaker)

                        #启动插件的时候控制肢体shakeshake和头部灯光blingbling （再来句插件启动语,嘿嘿）
                        if('robot_open_shake_bling' in self.config
                                and self.config['robot_open_shake_bling']=="yes"):
                            #木有IPC，后台单独运行一小会儿就结束了，直接创建daemon进程Led
                            led_son_processor = Process(target=lib.util.create_daemon, 
                                    args=(Led.get_instance().bling,(3,)))
                            led_son_processor.start()
                            led_son_processor.join()

                            #主进程shake
                            #gpioManager.shakeshake( son_process_callback=self.speaker.say, process_args=(text,), shake_num=0)

                if ((plugin.isValid(text) or self.isValidPluginInstruction(plugin,text))
                        and plugin.TAG in self.in_to_fps
                        and plugin.TAG in self.out_from_fps
                        and plugin.TAG in self.son_processors
                        and self.getPluginPid(plugin) == self.son_processors[plugin.TAG].pid):
                    self._logger.debug("'%s' is a valid phrase for plugin " + "'%s'", text, plugin.CATE+"_"+plugin.__name__)
                    try:
                        in_to_fp = self.in_to_fps[plugin.TAG]
                        out_from_fp = self.out_from_fps[plugin.TAG]
                        son_processor = self.son_processors[plugin.TAG]
                        plugin.process_handle(text,in_to_fp,out_from_fp,son_processor,self.speaker)
                    except Exception:
                        self._logger.error('Failed to send valid word %s to pipe for %s', text,plugin.CATE+"_"+plugin.__name__,exc_info=True)
                        #self.speaker.say("遇到一些麻烦，请重试一次")
                    else:
                        self._logger.debug("Send Pipe Handling of phrase '%s' by " + "plugin '%s' completed", text, plugin.CATE+"_"+plugin.__name__)
                    finally:
                        return True
        self._logger.debug("No plugin was able to handle any of these " + "phrases: %r", texts)
        if self.ai_chat is None:
            self.speaker.say("您说的是"+text.encode('UTF-8')+"吗，我可能没有听清楚")
        return False

        
    @classmethod
    def getPluginPid(cls,plugin):
        pid = None 
        pid_path = os.path.join(lib.appPath.DATA_PATH, plugin.CATE+"_"+plugin.__name__+'.pid');
        if os.path.exists(pid_path):
            with open(pid_path,"r") as f:
                pid = int(f.read())
        return pid 

    def isValidPluginInstruction(self,plugin,text):
        '''
        验证text是否是插件引导词有效
        '''
        begin_instruction = self.config['plugins'][plugin.CATE][plugin.TAG]['begin_instruction']
        instruction = self.config['plugins'][plugin.CATE][plugin.TAG]['instruction']
        over_instruction = self.config['plugins'][plugin.CATE][plugin.TAG]['over_instruction']
        instructions = ",".join([begin_instruction,instruction,over_instruction])
        instructions = [word.replace(' ','') for word in instructions.split(',') if word.replace(' ','') != ""]
        instructions = list(set(instructions))
        self._logger.debug("instructions in %s %s: %s",plugin.CATE,plugin.TAG,','.join(instructions).encode("UTF-8"))
        
        res = any(word in text for word in instructions)
        
        return res
