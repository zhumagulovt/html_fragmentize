import click
from typing import Generator

from bs4 import BeautifulSoup, Tag, NavigableString, PageElement

MAX_LEN = 4096

BLOCK_TAGS = ["p", "b", "strong", "i", "ul", "ol", "div", "span"]


def read_file(source: str) -> str:
    try:
        message: str
        with open(source, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise click.FileError(source, "File not found")


def split_message(source: str, max_len=MAX_LEN) -> Generator[str, None, None]:
    """Splits the original message (`source`) into fragments of the specified length
    (`max_len`)."""
    message = read_file(source)
    soup = BeautifulSoup(message, "html.parser")
    total_length = 0
    element = soup
    while True:
        if len(str(soup)) < max_len:
            yield str(soup)
            return
        can_split_element = can_split_tag(element)
        if (
            isinstance(element, Tag)
            and can_split_element
            or isinstance(element, BeautifulSoup)
        ):
            element_closing_tag_length = 0
            parents = element.find_parents()

            # if element is not a soup and has parents
            if isinstance(element, Tag) and len(parents) > 1:
                closing_tag = get_closing_tag(element)
                element_closing_tag_length = len(closing_tag)
                parents = element.find_parents()
                parents.pop()
                for parent in parents:
                    closing_tag = get_closing_tag(parent)
                    element_closing_tag_length += len(closing_tag)

            for content in element.contents:
                total_length += len(str(content))

                if total_length + element_closing_tag_length >= max_len:
                    total_length -= len(str(content))
                    if can_split_tag(content):
                        opening_tag = get_opening_tag(content)
                        total_length += len(opening_tag)
                    element = content
                    break

        elif isinstance(element, Tag) and not can_split_element:

            fragment, soup = split_soup_from_element(
                soup, element, total_length, max_len
            )
            total_length = 0

            element = soup

            yield fragment
        else:
            fragment, soup = split_soup_from_element(
                soup, element, total_length, max_len
            )
            total_length = 0
            element = soup

            yield fragment


def split_soup_from_element(
    soup: BeautifulSoup, element: Tag | NavigableString, total_length: int, max_len: int
) -> tuple[str, BeautifulSoup]:
    while True:
        closing_tags = ""
        element = get_previous_element(element)
        parents = element.find_parents()
        parents.pop()
        fragment = str(soup)[:total_length]
        for parent in parents:
            closing_tag = get_closing_tag(parent)
            closing_tags += closing_tag

        if len(fragment) + len(closing_tags) > max_len:
            total_length -= len(str(element))
        else:
            fragment += closing_tags
            break

    new_fragment = ""
    for parent in reversed(parents):
        opening_tag = get_opening_tag(parent)
        new_fragment += opening_tag
    new_fragment += str(soup)[total_length:]
    soup = BeautifulSoup(new_fragment, "html.parser")

    return fragment, soup


def get_opening_tag(element: Tag) -> str:

    attrs = " ".join([f'{key}="{value}"' for key, value in element.attrs.items()])
    open_tag = f"<{element.name}{' ' + attrs if attrs else ''}>"

    return open_tag


def get_closing_tag(element: Tag) -> str:
    return f"</{element.name}>"


def get_previous_element(element: PageElement) -> PageElement:
    if element.previous_sibling is None:
        if element.parent.previous_sibling is None:
            element = element.previous_element
        else:
            element = element.parent.previous_sibling
    else:
        element = element.previous_sibling

    return element


def can_split_tag(tag: Tag) -> bool:
    """
    Check if we can split tag.

    If tag is in BLOCK_TAGS, but has only one child, that is text, we cannot split it
    """
    if not isinstance(tag, Tag):
        return False

    return tag.name in BLOCK_TAGS and not (
        len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString)
    )


@click.command()
@click.argument("source")
@click.option("--max-len", default=MAX_LEN, help="Message maximum length")
def main(source: str, max_len: int = MAX_LEN) -> None:
    for i, fragment in enumerate(split_message(source, max_len)):
        print(f"fragment: #{i}: {len(fragment)} chars")


if __name__ == "__main__":
    main()
