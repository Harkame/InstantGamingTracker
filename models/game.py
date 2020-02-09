import os


class Game:
    def __init__(self):
        self.code = ""
        self.title = ""
        self.price = 0.0
        self.url = ""
        self.available = False
        self.reduction = False

    def __str__(self):
        to_string = ""

        to_string += "Code :"
        to_string += self.code
        to_string += os.linesep
        to_string += os.linesep

        to_string += "Title : "
        to_string += self.title
        to_string += os.linesep
        to_string += os.linesep

        to_string += "Price : "
        to_string += self.price
        to_string += os.linesep
        to_string += os.linesep

        to_string += "Url : "
        to_string += self.url
        to_string += os.linesep
        to_string += os.linesep

        return to_string
