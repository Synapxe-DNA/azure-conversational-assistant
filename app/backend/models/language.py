from enum import Enum


class LanguageSelected(Enum):
    ENGLISH = "english"
    CHINESE = "chinese"
    MALAY = "malay"
    TAMIL = "tamil"
    SPOKEN = "spoken"


class LanguageBCP47:
    language_mapping = {
        LanguageSelected.ENGLISH.value: "en-US",
        LanguageSelected.CHINESE.value: "zh-CN",
        LanguageSelected.MALAY.value: "ms-MY",
        LanguageSelected.TAMIL.value: "ta-IN",
    }

    voice_mapping = {
        LanguageSelected.ENGLISH.value: "en-US-EmmaNeural",
        LanguageSelected.CHINESE.value: "zh-CN-XiaoxiaoNeural",
        LanguageSelected.MALAY.value: "ms-MY-YasminNeural",
        LanguageSelected.TAMIL.value: "ta-SG-VenbaNeural",
    }
