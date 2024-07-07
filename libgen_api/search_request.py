import dataclasses
import enum
import urllib

import requests
import bs4


SEARCH_COLUMN_NAMES = [
    "ID",
    "Author",
    "Title",
    "Publisher",
    "Year",
    "Pages",
    "Language",
    "Size",
    "Extension",
    "Mirror_1",
    "Mirror_2",
    "Mirror_3",
    "Mirror_4",
    "Mirror_5",
    "Edit",
]


class SearchType(enum.Enum):
    TITLE = "title"
    AUTHOR = "author"
    ISBN = "isbn"


@dataclasses.dataclass(frozen=True)
class SearchRequest:
    query: str
    search_type: SearchType

    def __post_init__(self):
        if len(self.query) < 3:
            raise ValueError("Query is too short")

    @property
    def _query_parsed(self):
        return urllib.parse.quote(self.query)

    @property
    def search_url(self):
        if self.search_type == SearchType.TITLE:
            return f"https://libgen.is/search.php?req={self._query_parsed}&column=title"
        if self.search_type == SearchType.AUTHOR:
            return f"https://libgen.is/search.php?req={self._query_parsed}&column=author"
        if self.search_type == SearchType.ISBN:
            return f"https://libgen.is/search.php?req={self._query_parsed}&column=isbn"
        raise ValueError(
            f"Invalid search type. Must be one of {SearchType.__members__.keys()}. "
            f"Got {self.search_type}"
        )

    def get_search_page(self):
        return requests.get(self.search_url)

    def aggregate_request_data(self):
        search_page = self.get_search_page()
        soup = bs4.BeautifulSoup(search_page.text, "lxml")

        # Libgen results contain 3 tables
        # Table2: Table of data to scrape.
        information_table = soup.find_all("table")[2]

        return [self.extract_from_row(row) for row in information_table.find_all("tr")[1:]]

    def extract_from_row(self, row: bs4.Tag):
        columns = row.find_all("td")
        data = {}
        data["ID"] = columns[0].text
        data["Author"] = columns[1].text
        # For the title, we need to make sure we remove any i tags
        data = {**data, **self.get_series(columns[2])}
        data = {**data, **self.get_edition_and_isbn(columns[2])}
        # The get_title method modifies the column, so make sure this is the last thing we do to
        # that column
        data['Title'] = self.get_title(columns[2])
        data["Publisher"] = columns[3].text
        data["Year"] = columns[4].text
        data["Pages"] = columns[5].text
        data["Language"] = columns[6].text
        data["Size"] = columns[7].text
        data["Extension"] = columns[8].text
        # Get all the links in the last column
        links = [a["href"] for c in columns[9:11] for a in c.find_all("a")]
        data["Links"] = links[:-1]
        data["Edit"] = links[-1]

        return data

    def get_title(self, td):
        # Get the text of the last a tag, but remove any i tags that might be present
        a_tag = td.find_all("a")[-1]
        for i_tag in a_tag.find_all("i"):
            i_tag.decompose()
        return a_tag.text
    
    def get_series(self, td):
        # Find the first a tag
        a_tag = td.find_all("a")[0]
        # If column=series is in the href of the atag, return the text of the a tag
        if "series" in a_tag["href"]:
            return {"Series": a_tag.text}
        return {}
    
    def get_edition_and_isbn(self, td):
        # Find the last a tag
        a_tag = td.find_all("a")[-1]
        has_break = len(a_tag.find_all("br")) > 0
        i_tags = a_tag.find_all("i")
        if has_break and len(i_tags) == 1:
            return {"ISBN": i_tags[0].text}
        if has_break and len(i_tags) == 2:
            return {"Edition": i_tags[0].text, "ISBN": i_tags[1].text}
        if not has_break and len(i_tags) == 1:
            return {"Edition": i_tags[0].text}
        return {}
