# -*- coding: utf-8 -*-

import os
import yaml
import requests
import json

from abc import ABCMeta, abstractmethod
import lib

class BaseChat(object):
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    """
    __init__ params'name must be the same with config
    """
    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @classmethod
    @abstractmethod
    def is_available(cls):
        return True

    def __init__(self, **kwargs):
        self._logger = lib.util.init_logger(__name__)

    @classmethod
    def chat(self, texts, parsed):
        pass

    @classmethod
    def stream_chat(self, texts):
        pass


class OpenaiChat(BaseChat):
    TAG = "openai"

    def __init__(
        self,
        openai_api_key,
        model,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
        stop_ai,
        prefix="",
        proxy="",
        api_base="",
    ):
        super(self.__class__, self).__init__()

        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_api_key = openai_api_key
        self.openai_proxy = proxy
        self._logger.info("%s use proxy: %s" % (self.TAG,proxy,))

        self.model = model
        self.prefix = prefix
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop_ai = stop_ai
        self.api_base = api_base if api_base else "https://api.openai.com/v1/chat"
        self.context = []

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'openai.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        return config

    # just a simple requet stream chat for python2.7, if use openai sdk, need python3.7+
    def stream_chat(self, texts):
        msg = "".join(texts).decode("utf-8")
        msg = lib.util.stripPunctuation(msg)
        msg = self.prefix + msg  # add prefix prompt
        self._logger.info("msg: %s" % msg)
        self.context.append({"role": "user", "content": msg})

        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.openai_api_key,
        }

        data = {"model": self.model, "messages": self.context, "stream": True}
        self._logger.info("start stream request chat")
        url = self.api_base + "/completions"
        try:
            response = requests.request(
                "POST",
                url,
                headers=header,
                json=data,
                stream=True,
                proxies={"https": self.openai_proxy},
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response.iter_lines():
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data:") and line_str[5:]:
                        if line_str.startswith("data: [DONE]"):
                            break
                        line_json = json.loads(line_str[5:])
                        if "choices" in line_json:
                            if len(line_json["choices"]) > 0:
                                choice = line_json["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "role" in delta:
                                        role = delta["role"]
                                    elif "content" in delta:
                                        delta_content = delta["content"]
                                        i += 1
                                        if i < 40:
                                            self._logger.debug("delta_content: %s",delta_content)
                                        elif i == 40:
                                            self._logger.debug("......")
                                        one_message["content"] = (
                                            one_message["content"] + delta_content
                                        )
                                        yield delta_content

                    elif len(line_str.strip()) > 0:
                        self._logger.debug("line_str:%s",line_str)
                        yield line_str

        except Exception as e:
            ee = e
            def generate():
                yield "request error:\n" + str(ee)

        return generate

    def chat(self, texts, parsed):
        try:
            import openai
        except Exception as e:
            # critical exit
            self._logger.critical("import openai failed, need python3.7+")

        msg = "".join(texts)
        msg = lib.util.stripPunctuation(msg)
        msg = self.prefix + msg
        logger.info("msg: " + msg)
        try:
            respond = ""
            self.context.append({"role": "user", "content": msg})
            openai.api_key = self.openai_api_key
            openai.proxy = self.openai_proxy
            response = openai.Completion.create(
                model=self.model,
                messages=self.context,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=self.stop_ai,
                api_base=self.api_base
            )
            message = response.choices[0].message
            respond = message.content
            self.context.append(message)
            return respond
        except openai.error.InvalidRequestError:
            self._logger.warning("token超出长度限制，丢弃历史会话")
            self.context = []
            return self.chat(texts, parsed)
        except Exception:
            self._logger.critical("openai robot failed to response for %r", msg, exc_info=True)
            return "抱歉，OpenAI 回答失败"

