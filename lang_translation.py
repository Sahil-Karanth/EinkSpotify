from pypinyin import lazy_pinyin
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from pykakasi import kakasi
import unicodedata

# Initialize Korean transliterator
hangul_trans = Transliter(academic)

# Initialize Japanese transliterator
jp_converter = kakasi()



def strip_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

# Character classification
def __detect_script(char):
    code = ord(char)
    if 0x4e00 <= code <= 0x9fff:  # CJK Unified Ideographs (mostly Chinese)
        return 'chinese'
    elif 0xac00 <= code <= 0xd7af:  # Hangul Syllables
        return 'korean'
    elif (0x3040 <= code <= 0x309f) or (0x30a0 <= code <= 0x30ff):  # Japanese Hiragana/Katakana
        return 'japanese'
    else:
        return 'other'  # English, numbers, punctuation, etc.

# Transliterate chunk
def __transliterate_chunk(chunk, lang):
    if lang == 'chinese':
        return ''.join(lazy_pinyin(chunk))
    elif lang == 'korean':
        return hangul_trans.translit(chunk)
    elif lang == 'japanese':
        result = jp_converter.convert(chunk)
        return ''.join([item['hepburn'] for item in result])
    else:
        # latin language accents
        return strip_accents(chunk)

# Main transliteration function
def transliterate_mixed(text):
    result = []
    buffer = ''
    current_lang = None

    for char in text:
        lang = __detect_script(char)
        if lang != current_lang:
            if buffer:
                result.append(__transliterate_chunk(buffer, current_lang))
                buffer = ''
            current_lang = lang
        buffer += char

    if buffer:
        result.append(__transliterate_chunk(buffer, current_lang))

    return ''.join(result)

if __name__ == "__main__":
    text = "Hello 世界, 안녕하세요! 日本語テスト."
    output = transliterate_mixed(text)
    print(output)
