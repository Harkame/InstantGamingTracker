import unicodedata


def format_string(base_string="", title="", price="", url=""):
    return (
        base_string.replace("$title", title)
        .replace("$price", price)
        .replace("$url", url)
    )


def strip_accents(text):

    try:
        text = unicode(text, "utf-8")
    except NameError:
        pass

    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")

    return str(text)
