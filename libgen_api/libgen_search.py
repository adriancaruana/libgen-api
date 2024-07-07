import dataclasses
import enum

import requests
from bs4 import BeautifulSoup

from .search_request import SearchRequest, SearchType

MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io", "Infura"]


@dataclasses.dataclass(frozen=True)
class LibgenSearch:
    search_type: SearchType

    def search(self, query):
        search_request = SearchRequest(query, search_type=self.search_type)
        return search_request.aggregate_request_data()

    def search_filtered(self, query, filters, exact_match=True):
        search_request = SearchRequest(query, search_type=self.search_type)
        results = search_request.aggregate_request_data()
        filtered_results = self.filter_results(
            results=results,
            filters=filters,
            exact_match=exact_match,
        )
        return filtered_results

    def resolve_download_links(self, item):
        mirror_1 = item["Links"][0]
        page = requests.get(mirror_1)
        soup = BeautifulSoup(page.text, "html.parser")
        links = soup.find_all("a", string=MIRROR_SOURCES)
        download_links = {link.string: link["href"] for link in links}
        return download_links

    def filter_results(self, results, filters, exact_match):
        """
        Returns a list of results that match the given filter criteria.
        When exact_match = true, we only include results that exactly match
        the filters (ie. the filters are an exact subset of the result).

        When exact-match = false,
        we run a case-insensitive check between each filter field and each result.

        exact_match defaults to TRUE -
        this is to maintain consistency with older versions of this library.
        """

        filtered_list = []
        if exact_match:
            for result in results:
                # check whether a candidate result matches the given filters
                if filters.items() <= result.items():
                    filtered_list.append(result)

        else:
            filter_matches_result = False
            for result in results:
                for field, query in filters.items():
                    if query.casefold() in result[field].casefold():
                        filter_matches_result = True
                    else:
                        filter_matches_result = False
                        break
                if filter_matches_result:
                    filtered_list.append(result)

        return filtered_list

