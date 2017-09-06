# -*- coding: utf-8-*-
import pkgutil

import lib.appPath
import lib.util

class Bootstrap(object):

    def __init__(self, speaker, config):
        """
        加载插件，通过指令引导执行对应插件模块
        """
        self.speacker = speacker
        self.config = config
        self.plugins = self.get_plugins()
        self._logger = lib.util.init_logger(__name__)

    @classmethod
    def get_plugins(cls):
        """
        通过引导配置获取插件模块，通过插件模块中的PRIORITY属性控制优先级，按大到小排序，越大越优先
        """
        plugins = []
        locations = []
        tags = []
        if "plugins" in self.config:
            for (cate,plugin_tags) in self.config['plugins'].items():
                locations.append(os.path.join(lib.appPath.PLUGIN_PATH,cate))
                tags.append(plugin_tags)

        self._logger.debug("Looking for plugins in: %s", ', '.join(["'%s'" % location for location in locations]))
        self._logger.debug("Looking for tags : %s", ','.join(tags))

        tags = ','.join(tags).split(',')

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_plugin(name)
                plugin = loader.load_plugin(name)
            except:
                self._logger.warning("Skipped plugin '%s' due to an error.", name, exc_info=True)
            else:
                if ( (hasattr(plugin, 'isValid')) and (hasattr(plugin, 'handle')) 
                        and (hasattr(plugin, 'TAG')) and (plugin.TAG in tags) ):
                    self._logger.debug("Found plugin '%s' with tag: %r", name, plugin.TAG)
                    plugins.append(mod)
                else:
                    self._logger.warning("Skipped plugin '%s' because it misses " + "the TAG constant.", name)

        plugins.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY') else 0, reverse=True)

        return plugins

    def query(self, texts):
        """
        引导识别的texts给对应的插件处理
        """
        for plugin in self.plugins:
            for text in texts:
                if plugin.isValid(text):
                    self._logger.debug("'%s' is a valid phrase for plugin " + "'%s'", text, plugin.__name__)
                    try:
                        plugin.handle(text, self.speacker)
                    except Exception:
                        self._logger.error('Failed to execute plugin', exc_info=True)
                        self.speacker.say("遇到一些麻烦，请重试一次")
                    else:
                        self._logger.debug("Handling of phrase '%s' by " + "plugin '%s' completed", text, plugin.__name__)
                    finally:
                        return
        self._logger.debug("No plugin was able to handle any of these " + "phrases: %r", texts)
