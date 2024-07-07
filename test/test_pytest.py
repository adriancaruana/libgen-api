import pytest
from libgen_api.libgen_search import LibgenSearch, SearchType

title = "Pride and Prejudice"
author = "Agatha Christie"
isbn = "9781562545291"


@pytest.fixture
def title_search():
    return LibgenSearch(SearchType.TITLE)

@pytest.fixture
def author_search():
    return LibgenSearch(SearchType.AUTHOR)

@pytest.fixture
def isbn_search():
    return LibgenSearch(SearchType.ISBN)


class TestBasicSearching:
    def test_title_search(self, title_search):
        results = title_search.search(title)
        first_result = results[0]

        assert title in first_result["Title"]

    def test_author_search(self, author_search):
        results = author_search.search(author)
        first_result = results[0]

        assert author in first_result["Author"]

    def test_isbn_search(self, isbn_search):
        results = isbn_search.search(isbn)
        print(results)
        first_result = results[0]

        assert isbn in first_result["ISBN"]

    def test_title_filtering(self, title_search):
        title_filters = {"Year": "2007", "Extension": "epub"}
        titles = title_search.search_filtered(title, title_filters, exact_match=True)
        first_result = titles[0]

        assert (title in first_result["Title"]) & fields_match(
            title_filters, first_result
        )

    def test_author_filtering(self, author_search):
        author_filters = {"Language": "German", "Year": "2009"}
        titles = author_search.search_filtered(author, author_filters, exact_match=True)
        first_result = titles[0]

        assert (author in first_result["Author"]) & fields_match(
            author_filters, first_result
        )

    # explicit test of exact filtering
    # should return no results as they will all get filtered out
    def test_exact_filtering(self, author_search):
        exact_filters = {"Extension": "PDF"}
        # if exact_match = True, this will filter out all results as
        # "pdf" is always written lower case on Library Genesis
        titles = author_search.search_filtered(author, exact_filters, exact_match=True)

        assert len(titles) == 0

    def test_non_exact_filtering(self, author_search):
        non_exact_filters = {"Extension": "PDF"}
        titles = author_search.search_filtered(author, non_exact_filters, exact_match=False)
        first_result = titles[0]

        assert (author in first_result["Author"]) & fields_match(
            non_exact_filters, first_result, exact=False
        )

    def test_non_exact_partial_filtering(self, title_search):
        partial_filters = {"Extension": "p", "Year": "200"}
        titles = title_search.search_filtered(title, partial_filters, exact_match=False)
        first_result = titles[0]

        assert (title in first_result["Title"]) & fields_match(
            partial_filters, first_result, exact=False
        )

    def test_exact_partial_filtering(self, title_search):
        exact_partial_filters = {"Extension": "p"}
        titles = title_search.search_filtered(
            title, exact_partial_filters, exact_match=True
        )

        assert len(titles) == 0

    def test_resolve_download_links(self, author_search):
        titles = author_search.search(author)
        title_to_download = titles[0]
        dl_links = author_search.resolve_download_links(title_to_download)

        # ensure each host is in the results and that they each have a url
        assert (["GET", "Cloudflare", "IPFS.io"] == list(dl_links.keys())) & (
            False not in [len(link) > 0 for key, link in dl_links.items()]
        )

    # should return an error if search query is less than 3 characters long
    def test_raise_error_on_short_search(self, title_search):
        with pytest.raises(ValueError):
            titles = title_search.search(title[0:2])

####################
# Helper Functions #
####################

# Check object fields for equality -
# -> Returns True if they match.
# -> Returns False otherwise.
#
# when exact-True, fields are checked strictly (==).
#
# when exact=False, fields are normalized to lower case,
# and checked whether filter value is a subset of the response.
def fields_match(filter_obj, response_obj, exact=True):
    for key, value in filter_obj.items():

        if exact is False:
            value = value.lower()
            response_obj[key] = response_obj[key].lower()
            if value not in response_obj[key]:
                return False

        elif response_obj[key] != value:
            return False
    return True
