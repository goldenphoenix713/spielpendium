"""Base HTTP client logic for the BoardGameGeek API."""

from __future__ import annotations

import time
import urllib.parse
from typing import Any
from xml.parsers.expat import ExpatError

import requests
import xmltodict
from loguru import logger as log
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    BGG_API_TOKEN,
    BGG_API_URL,
    MAX_API_CHECKS,
    TIME_BETWEEN_API_CHECKS,
)

# Set up global requests session for BGG API calls
bgg_api_retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
)
bgg_api_adapter = HTTPAdapter(
    max_retries=bgg_api_retry_strategy, pool_connections=10, pool_maxsize=10
)

bgg_session = requests.Session()
bgg_session.mount("http://", bgg_api_adapter)
bgg_session.mount("https://", bgg_api_adapter)


def get_xml_info(
    url: str, query: dict[str, str] | None = None
) -> dict[str, Any]:
    """Pulls XML info from the web and converts it to a dict.

    :param url: The URL that will be pulled to get XML data.
    :type url: str
    :param query: A dictionary containing query parameters for the get request.
    :type query: dict[str, str]
    :raises requests.exceptions.HTTPError: If there's any error in retrieving
            data at the URL.
    :raises xmltodict.expat.ExpatError: If the retrieved data cannot be
            converted to a dict
    :return: The information from the XML converted into a dict.
    :rtype: dict[str, Any]
    """

    data: dict[str, Any] = {}

    for ii in range(MAX_API_CHECKS):
        response = bgg_session.get(
            url,
            params=query,
            headers={"Authorization": f"Bearer {BGG_API_TOKEN}"},
        )
        # Code 202 means data is still being generated
        if response.status_code == 202:
            log.info(
                f"Waiting for API to generate data at {url}. "
                f"Next check in {TIME_BETWEEN_API_CHECKS} seconds"
            )
            time.sleep(TIME_BETWEEN_API_CHECKS)
            continue

        # Handle 429 Too Many Requests
        if response.status_code == 429:
            sleep_duration = TIME_BETWEEN_API_CHECKS * (2**ii)
            log.warning(
                f"Rate limited (429) at {url}. "
                f"Retrying (attempt {ii + 1}/{MAX_API_CHECKS}) in {sleep_duration} seconds..."
            )
            time.sleep(sleep_duration)
            continue

        # If we reach here, it's not a 202 or 429. If it's not 200 either,
        # quit (error)
        if response.status_code != 200:
            log.error(
                f"API did not generate data at {url} after "
                f"checking {MAX_API_CHECKS} times. "
                f"Status code: {response.status_code}"
            )
            response.raise_for_status()

        data_bytes = response.content
        log.debug(f"Information retrieved successfully from {url}.")

        # Convert the bytes object to a dict.
        try:
            data = xmltodict.parse(data_bytes)
            log.debug("Data successfully converted to dict.")
            return data
        except ExpatError as e:
            log.error(f"Failed to parse XML from {url}: {e}.")
            if ii < MAX_API_CHECKS - 1:
                time.sleep(TIME_BETWEEN_API_CHECKS)
                continue
            else:
                raise

    return data


def search_bgg(search_query: str, exact_flag: bool = False) -> dict[str, Any]:
    """Assembles the search URL and returns data from the BoardGameGeek API.

    :param search_query: The query to search for.
    :type search_query: str
    :param exact_flag: A flag that tells the BGG API whether to only return
        exact matches or not.
    :type exact_flag: bool
    :return: Dictionary with the search results.
    :rtype: dict[str, Any]
    """
    search_query = urllib.parse.quote(search_query)
    search_url = f"{BGG_API_URL}search"

    query = {"query": search_query, "exact": str(int(exact_flag))}
    return get_xml_info(search_url, query)
