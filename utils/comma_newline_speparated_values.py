from typing import Generator


class CommaNewLineSeparatedValues:
    """
    Mostly like csv but instead of "," separator used ",\n"
    """

    def _read_value(self, start: int, content: str) -> tuple[int, str]:
        """
        Reads value,
        returns next index of next character
        after separator and value
        """
        value = ""
        for i in range(start, len(content)):
            if (char := content[i]) != "\n":
                value += char
                continue
            return i+1, value[:-1]
        return len(content), value

    def reader(self, content: str) -> Generator[list[str], None, None]:
        """
        Generator which yields group of values
        """
        start = 0
        while start < len(content):
            values = []
            # reading values until hit groups separator
            while start < len(content) and content[start] != "\n":
                start, value = self._read_value(start, content)
                values.append(value)
            yield values
            start += 1
