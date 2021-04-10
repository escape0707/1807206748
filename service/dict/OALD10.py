# -*- coding:utf-8 -*-
import random
import re
import enum
import pathlib
from typing import Optional

from ..base import *


class Dialect(enum.Enum):
    BRITISH = "gb"
    AMERICAN = "us"


PRONUNCIATION_PATTERN_TEMPLATE = r"sound://(\w*?__{dialect}_\d+.mp3)"
PATTERN_BY_DIALECT_COLLECTION = {
    dialect: re.compile(PRONUNCIATION_PATTERN_TEMPLATE.format(dialect=dialect.value))
    for dialect in Dialect
}
DICT_PATH: Optional[str] = None


@register(["MDX-OALD10", "MDX-OALD10"])
class OALD10(MdxService):
    def __init__(self):
        dict_path = DICT_PATH
        if not dict_path:
            from ...service import service_manager, service_pool

            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else ""
                service_pool.put(service)
                if title.startswith("牛津高阶英汉双解词典"):
                    dict_path = service.dict_path
                    break
        super(OALD10, self).__init__(dict_path)

    @property
    def title(self) -> str:
        return getattr(self, "__register_label__", self.unique)

    @export("HTML")
    def just_raw_html(self) -> str:
        html = self.get_html()
        pathlib.Path(r"C:\Users\tothe\Workspaces\lookup.html").write_text(
            html, encoding="utf-8"
        )
        return html

    @export("PHON")
    def why_i_cant_use_fld_phonetic(self) -> str:  # TODO
        html = self.get_html()
        m = self._PHONETIC_PATTERN.search(html)
        return f"[{m[1]}]" if m else ""

    @export("BRE_PRON")
    def field_pronunciation_british(self):
        return self._field_pronunciation(Dialect.BRITISH)

    @export("AME_PRON")
    def field_pronunciation_american(self):
        return self._field_pronunciation(Dialect.AMERICAN)

    @export("All examples with audios")
    def fld_sentence_audio(self):
        return self._range_sentence_audio([i for i in range(0, 100)])

    @export("Random example with audio")
    def fld_random_sentence_audio(self):
        return self._range_sentence_audio()

    @export("First example with audio")
    def fld_first1_sentence_audio(self):
        return self._range_sentence_audio([0])

    @export("First 2 examples with audios")
    def fld_first2_sentence_audio(self):
        return self._range_sentence_audio([0, 1])

    @staticmethod
    def _get_html_following_link(self) -> str:
        html: str = self.get_html()
        while html.startswith("@@@LINK="):
            self.word = html[8:]
            html = self.get_html()
        return html

    def _fld_audio(self, audio):
        name = get_hex_name("mdx-" + self.unique.lower(), audio, "mp3")
        name = self.save_file(audio, name)
        if name:
            return self.get_anki_label(name, "audio")
        return ""

    def _field_pronunciation(self, dialect: Dialect):
        """获取发音字段"""
        html = self.get_html()
        pronunciation_pattern = PATTERN_BY_DIALECT_COLLECTION[dialect]
        match = pronunciation_pattern.search(html)
        in_mdd_path = "/" + match[1]  # upstream don't use pathlib for this
        extract_to_path = pathlib.Path(f"OALD10-{self.word}.mp3")
        self.save_file(in_mdd_path, extract_to_path)
        return self.get_anki_label(extract_to_path, "audio")

    _PHONETIC_PATTERN = re.compile(r'<span class="phon">/(.*?)/</span>')

    def _range_sentence_audio(self, range_arr=None):
        m = self.get_html()
        if m:
            soup = parse_html(m)
            el_list = soup.findAll(
                "x-g-blk",
            )
            if el_list:
                maps = []
                for element in el_list:
                    sounds = element.find_all("a")
                    if sounds:
                        br_sound = "None"
                        us_sound = None
                        en_text = cn_text = ""
                        for sound in sounds:
                            if sound.find(["audio-gbs-liju", "audio-brs-liju"]):
                                br_sound = sound["href"][7:]
                            elif sound.find(["audio-uss-liju", "audio-ams-liju"]):
                                us_sound = sound["href"][7:]
                        try:
                            en_text = element.x["wd"]
                            cn_text = element.x.chn.contents[1]
                        except:
                            continue
                        if us_sound:  # I mainly use us_sound
                            maps.append([br_sound, us_sound, en_text, cn_text])

            my_str = ""
            range_arr = (
                range_arr if range_arr else [random.randrange(0, len(maps) - 1, 1)]
            )
            if maps:
                for i, e in enumerate(maps):
                    if i in range_arr:
                        br_sound = e[0]
                        us_sound = e[1]
                        en_text = e[2]
                        cn_text = e[3]
                        us_mp3 = self._fld_audio(us_sound)
                        if br_sound != "None":
                            br_mp3 = self._fld_audio(br_sound)
                        else:
                            br_mp3 = ""
                        # please modify the code here to get br_mp3
                        # my_str = my_str + br_mp3 + ' ' + en_text  + cn_text + '<br>'
                        # my_str = my_str + us_mp3 + en_text  + cn_text + '<br>'
                        my_str = my_str + br_mp3 + us_mp3 + en_text + cn_text + "<br>"
            return my_str
        return ""
