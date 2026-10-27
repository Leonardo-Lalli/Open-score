"""Minimise sensitive URLs in Uvicorn access logs, without changing requests."""

import logging
import re

TOKEN_PATH = re.compile(r"^(/(?:api/)?(?:v1/)?(?:invites|public)/)([^/]+)")


class PrivateAccessFilter(logging.Filter):
    def filter(self, record):
        # Uvicorn's h11/httptools access records use the same five arguments.
        if isinstance(record.args, tuple) and len(record.args) == 5:
            args = list(record.args)
            if isinstance(args[2], str):
                path = args[2].partition("?")[0].partition("#")[0]
                args[2] = TOKEN_PATH.sub(
                    lambda m: m[0] if m[2] in ("validate", "accept", "tournaments")
                    else m[1] + "[redacted]", path,
                )
                record.args = tuple(args)
        return True


def install_access_filter():
    logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, PrivateAccessFilter) for f in logger.filters):
        logger.addFilter(PrivateAccessFilter())
