"""Image handling for the BoardGameGeek API."""

from __future__ import annotations

import concurrent.futures

import requests
from loguru import logger as log
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import IMAGE_DIR


def get_images(
    images_data: tuple[int, str] | list[tuple[int, str]],
) -> dict[int, str | None]:
    """Retrieves images from a list of BGG IDs and URLs and saves them.

    :param images_data: A tuple or list of tuples containing (bgg_id, image_url).
    :type images_data: tuple[int, str] | list[tuple[int, str]]
    :return: A dictionary mapping bgg_id to image paths as strings (or None for failures).
    :rtype: dict[int, str | None]
    """
    # Convert to list
    if isinstance(images_data, tuple):
        images_data = [images_data]

    images: dict[int, str | None] = {}
    images_to_download: list[tuple[int, str]] = []

    for bgg_id, url in images_data:
        filename = f"{bgg_id}.jpg"
        image_path = IMAGE_DIR / filename
        if image_path.exists() and image_path.stat().st_size > 0:
            log.debug(
                f"Image for BGG ID {bgg_id} already exists (checked in get_images batching)."
            )
            images[bgg_id] = filename
        else:
            images_to_download.append((bgg_id, url))

    if not images_to_download:
        return images

    # Set up pool of subprocesses to each get an image
    # and configure a session with retry logic
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
    )

    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor,
        requests.Session() as session,
    ):
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Start the load operations and mark each future with its BGG ID
        future_to_bgg_id = {
            executor.submit(
                get_single_image, bgg_id, url, 60.0, session
            ): bgg_id
            for bgg_id, url in images_to_download
        }
        for future in concurrent.futures.as_completed(future_to_bgg_id):
            bgg_id = future_to_bgg_id[future]
            try:
                images[bgg_id] = future.result()
            except Exception as e:
                log.warning(
                    f"Failed to download image for BGG ID {bgg_id}: {e}"
                )
                images[bgg_id] = None

    return images


def get_single_image(
    bgg_id: int, image_url: str, timeout: float, session: requests.Session
) -> str | None:
    """Gets the image at the requested url and saves it to disk.

    :param bgg_id: The BGG ID used for naming the image file.
    :type bgg_id: int
    :param image_url: The image url.
    :type image_url: str
    :param timeout: The timeout in seconds.
    :type timeout: float
    :param session: The session to use.
    :return: The path of the image if successful, otherwise None.
    :rtype: str | None
    """

    filename = f"{bgg_id}.jpg"
    image_path = IMAGE_DIR / filename

    if image_path.exists() and image_path.stat().st_size > 0:
        log.debug(
            f"Image for BGG ID {bgg_id} already exists. Skipping download."
        )
        return filename

    # Do not send BGG API Token to image servers (usually cloudfront/S3)
    response = session.get(
        image_url,
        timeout=timeout,
    )

    if response.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(response.content)
        return filename
    else:
        log.error(
            f"Failed to fetch image from {image_url}. Status code: {response.status_code}"
        )
        raise requests.exceptions.HTTPError(
            f"Failed to fetch image: {response.status_code}"
        )
