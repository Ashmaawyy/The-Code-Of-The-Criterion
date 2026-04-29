"""Elasticsearch client factory for Al-Furqan.

Reads connection settings from AppConfig (or environment variables as
fallback) and returns a configured ``Elasticsearch`` instance.
"""

import logging
import os

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "http://localhost:9200"


def create_es_client(
    hosts: list[str] | None = None,
    request_timeout: int = 30,
    verify_certs: bool = True,
) -> Elasticsearch:
    """Create and return an Elasticsearch client.

    Resolution order for hosts:
        1. Explicit ``hosts`` argument
        2. ``ELASTICSEARCH_URL`` environment variable
        3. Default ``http://localhost:9200``
    """
    if hosts is None:
        env_url = os.environ.get("ELASTICSEARCH_URL")
        hosts = [env_url] if env_url else [_DEFAULT_HOST]

    client = Elasticsearch(
        hosts=hosts,
        request_timeout=request_timeout,
        verify_certs=verify_certs,
    )

    # Quick connectivity check
    if not client.ping():
        logger.warning("Elasticsearch ping failed for hosts=%s", hosts)
    else:
        info = client.info()
        logger.info(
            "Connected to Elasticsearch %s at %s",
            info["version"]["number"],
            hosts,
        )

    return client
