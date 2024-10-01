from lingua import Language, LanguageDetectorBuilder
from opentelemetry import trace

# Get the global tracer provider
tracer = trace.get_tracer(__name__)


class Utils:
    """
    Utility function to get the language of the query text if language selected is "spoken"
    """

    @staticmethod
    def get_language(query_text: str):
        languages = [Language.ENGLISH, Language.CHINESE, Language.TAMIL, Language.MALAY]
        detector = LanguageDetectorBuilder.from_languages(*languages).build()
        language = detector.detect_language_of(query_text)
        if language is None:
            language = "english"
            print("Language not detected. Defaulting to English.")
        else:
            language = str(language).split(".")[1].lower()  # get language name from enum
        return language
