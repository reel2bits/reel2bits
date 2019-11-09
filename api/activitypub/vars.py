from enum import Enum
from little_boxes.activitypub import CTX_AS, CTX_SECURITY


class Box(Enum):
    INBOX = "inbox"
    OUTBOX = "outbox"
    REPLIES = "replies"


HEADERS = [
    "application/activity+json",
    "application/ld+json;profile=https://www.w3.org/ns/activitystreams",
    'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    "application/ld+json",
]

DEFAULT_CTX = [
    CTX_AS,
    CTX_SECURITY,
    {
        # AS ext
        "Hashtag": "as:Hashtag",
        "sensitive": "as:sensitive",
        "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
        # toot
        "toot": "http://joinmastodon.org/ns#",
        "featured": "toot:featured",
        # schema
        "schema": "http://schema.org#",
        "PropertyValue": "schema:PropertyValue",
        "value": "schema:value",
        # Our custom stuff
        "reel2bits": {
            "@context": {
                # This page intentionally left blank.
            }
        },
        "licence": "reel2bits:licence",
        "genre": "reel2bits:genre",
        "tags": "reel2bits:tags",
        "artwork": "reel2bits:artwork",
        "transcoded": "reel2bits:transcoded",
        "transcode_url": "reel2bits:transcode_url",
    },
]
