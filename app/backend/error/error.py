import error.error_config as error_config
from models.language import LanguageSelected as LS
from openai import APIError

SELF_HARM_MESSAGE_FILTER = {
    LS.ENGLISH.value: error_config.self_harm_english,
    LS.CHINESE.value: error_config.self_harm_chinese,
    LS.MALAY.value: error_config.self_harm_malay,
    LS.TAMIL.value: error_config.self_harm_tamil,
}

FILTERED_CONTEXT_MESSAGE = {
    LS.ENGLISH.value: error_config.filtered_content_english,
    LS.CHINESE.value: error_config.filtered_content_chinese,
    LS.MALAY.value: error_config.filtered_content_malay,
    LS.TAMIL.value: error_config.filtered_content_tamil,
}

EXCEED_CONTEXT_LENGTH_MESSAGE = {
    LS.ENGLISH.value: error_config.exceed_context_length_english,
    LS.CHINESE.value: error_config.exceed_context_length_chinese,
    LS.MALAY.value: error_config.exceed_context_length_malay,
    LS.TAMIL.value: error_config.exceed_context_length_tamil,
}


def error_response(error: Exception, language: str = None) -> dict:
    if isinstance(error, APIError):
        if error.code == "content_filter":
            if error.body["innererror"]["content_filter_result"]["self_harm"]["filtered"]:
                error_msg = SELF_HARM_MESSAGE_FILTER[language]
            else:
                error_msg = FILTERED_CONTEXT_MESSAGE[language]
        elif error.code == "context_length_exceeded":
            error_msg = EXCEED_CONTEXT_LENGTH_MESSAGE[language]
        else:
            error_msg = str(error)

    else:
        error_msg = str(error)
    return {"error": error_msg}
