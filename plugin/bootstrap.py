# -*- coding: utf-8-*-
import os
import pkgutil

import lib.appPath
import lib.util

class Bootstrap(object):

    def __init__(self, speaker, config):
        """
        加载插件，通过指令引导执行对应插件模块
        """
        self._logger = lib.util.init_logger(__name__)
        self.speaker = speaker
        self.config = config
        self.plugins = self.get_plugins(config)

        self.son_processors = {}
        self.in_fps = {}
        for plugin in self.plugins:
            out_fp, in_fp = Pipe(True)
            son_process = Process(target=self.son_process, args=(speaker,(out_fp, in_fp), plugin.son_process_handle))
            son_process.start()
            # 等pipe被fork 后，关闭主进程的输出端; 创建的Pipe一端连接着主进程的输入，一端连接着子进程的输出口
            out_fp.close()
            self.son_processors[plugin.TAG] = son_process
            self.in_fps[plugin.TAG] = in_fp

    @classmethod
    def son_process(cls, speaker, pipe, handle_callback=None):
        '''
        handle_callback 为轮训获取pipe中的数据进行相应逻辑处理函数,参数为从pipe中获取通信数据的回调函数,speaker为voice实例(tts)
        '''
        _out_fp, _in_fp = pipe
    
        # 关闭fork过来的输入端
        _in_fp.close()
        if handle_callback is not None:
            handle_callback(_out_fp,speaker)

    @classmethod
    def get_plugins(cls,config):
        """
        通过引导配置获取插件模块，通过插件模块中的PRIORITY属性控制优先级，按大到小排序，越大越优先
        """
        plugins = []
        locations = []
        tags = []
        logger = lib.util.init_logger(__name__)
        if "plugins" in config:
            for (cate,plugin_tags) in config['plugins'].items():
                locations.append(os.path.join(lib.appPath.PLUGIN_PATH,cate))
                tags.extend(plugin_tags.keys())

        tags = list(set(tags))

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                plugin = loader.load_module(name)
            except:
                logger.warning("Skipped plugin '%s' due to an error.", name, exc_info=True)
            else:
                if ( (hasattr(plugin, 'isValid')) 
                    and (hasattr(plugin, 'send_handle')) 
                    and (hasattr(plugin, 'son_process_handle')) 
                    and (hasattr(plugin, 'TAG')) and (plugin.TAG in tags) ):
                    logger.debug("Found plugin '%s' with tag: %r", name, plugin.TAG)
                    plugins.append(plugin)
                else:
                    logger.warning("Skipped plugin '%s' because it misses " + "the TAG constant.", name)

        plugins.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY') else 0, reverse=True)

        return plugins

    def query(self, queue=None):
        """
        引导识别的texts给对应的插件处理
        """
        texts = queue.get(True)
        for plugin in self.plugins:
            for text in texts:
                self._logger.debug("Started to bootstrap asr word to plunin %s with input:%s", plugin, text)
                text = lib.util.filt_punctuation(text)
                if plugin.isValid(text):
                    self._logger.debug("'%s' is a valid phrase for plugin " + "'%s'", text, plugin.__name__)
                    try:
                        self._logger.debug("send valid word %s to pipe for %s", text, plugin.__name__)
                        in_fp = self.in_fps[plugin.Tag]
                        son_processor = self.son_processors[plugin.Tag]
                        plugin.send_handle(text, in_fp,son_processor)
                    except Exception:
                        self._logger.error('Failed to send valid word %s to pipe for %s', text,plugin.__name__,exc_info=True)
                        #self.speaker.say("遇到一些麻烦，请重试一次")
                    else:
                        self._logger.debug("Send Pipe Handling of phrase '%s' by " + "plugin '%s' completed", text, plugin.__name__)
                    finally:
                        return
        self._logger.debug("No plugin was able to handle any of these " + "phrases: %r", texts)

    def checkSonProcessIsOver(cls,tag):
        pass
            
