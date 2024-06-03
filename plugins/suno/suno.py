# encoding:utf-8
import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *


@plugins.register(
    name="Suno",
    desire_priority=-1,
    hidden=True,
    desc="suno api plugin",
    version="1.0",
    author="Jolc",
)
class Suno(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            if not self.config:
                self._load_config_template()
            logger.info("[Suno] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[Suno]初始化异常：{e}")
            raise "[Suno] init failed, ignore "

    def on_handle_context(self, e_context: EventContext):
        context_type = e_context["context"].type
        if context_type != ContextType.TEXT:
            return
        content = e_context["context"].content
        plugin_prefix = self.config.get("prefix")
        enabled = self.config.get("enabled")
        if content.startswith(plugin_prefix) and enabled:
            content = content.replace(plugin_prefix, "", 1)
            reply = Reply()
            reply.type = ReplyType.TEXT
            e_context["reply"] = reply
            try:
                ids = self.request_suno(content.strip())
                if ids:
                    msg = "\n".join(ids)
                    reply.content = f"正在努力作曲中，请稍后点击链接试听吧！\n{msg}"
                else:
                    reply.content = "作曲失败，请稍后重试吧！"
            except Exception as e:
                logger.error(f"[Suno] error, msg={e}")
                reply.content = "作曲失败，请稍后重试吧！"
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def request_suno(self, content):
        url = f"{self.config.get('server')}/generate/description-mode"
        payload = json.dumps({
            "gpt_description_prompt": content,
            "mv": self.config.get("mv"),
            "prompt": self.config.get("prompt"),
            "make_instrumental": self.config.get("make_instrumental")
        })
        headers = {
            'Content-Type': 'application/json'
        }
        res = requests.post(url, headers=headers, data=payload, timeout=(5, 300))
        if res.status_code == 200:
            res = res.json()
            logger.debug(f"[Suno] res={res}")
            ids = []
            clips = res.get("clips")
            if clips:
                for clip in res.get("clips"):
                    ids.append(self.config.get("share_link") + "/" + clip.get("id"))
            return ids
        else:
            res_json = res.json()
            logger.error(f"[Suno] error, status_code={res.status_code}, msg={res_json.get('detail')}")
            return []

    def get_help_text(self, **kwargs):
        plugin_prefix = self.config.get("prefix")
        return f"输入：{plugin_prefix} 赫本的风，我会为您作曲"

    def _load_config_template(self):
        logger.debug("No Suno plugin config.json, use plugins/suno/config.json.template")
        try:
            plugin_config_path = os.path.join(self.path, "config.json.template")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    return plugin_conf
        except Exception as e:
            logger.exception(e)
