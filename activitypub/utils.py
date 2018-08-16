from flask import current_app
from little_boxes.activitypub import ActivityType
from little_boxes import activitypub as ap
from typing import Dict, Any

ObjectType = Dict[str, Any]


def ap_url(klass, username):
    if klass == "url":
        return f"https://{current_app.config['AP_DOMAIN']}/user/{username}"
    elif klass == "shared_inbox":
        return f"https://{current_app.config['AP_DOMAIN']}/inbox"
    elif klass == "inbox":
        return f"https://{current_app.config['AP_DOMAIN']}" f"/user/{username}/inbox"
    elif klass == "outbox":
        return f"https://{current_app.config['AP_DOMAIN']}" f"/user/{username}/outbox"
    else:
        return None


def full_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    root = current_app.config["AP_DOMAIN"]
    if path.startswith("/"):
        return root + path[1:]
    elif path.startswith("/"):
        return root + "/" + path
    else:
        return root + path


def embed_collection(total_items, first_page_id):
    """Helper creating a root OrderedCollection
     with a link to the first page."""
    return {
        "type": ap.ActivityType.ORDERED_COLLECTION.value,
        "totalItems": total_items,
        "first": f"{first_page_id}?page=first",
        "id": first_page_id,
    }


def add_extra_collection(item: Dict[str, Any]) -> Dict[str, Any]:
    if item["type"] != ActivityType.CREATE.value:
        return item

    item["object"]["replies"] = embed_collection(
        item.get("meta", {}).get("count_direct_reply", 0), f'{item["remote_id"]}/replies'
    )

    item["object"]["likes"] = embed_collection(item.get("meta", {}).get("count_like", 0), f'{item["remote_id"]}/likes')

    item["object"]["shares"] = embed_collection(
        item.get("meta", {}).get("count_boost", 0), f'{item["remote_id"]}/shares'
    )

    return item


def remove_context(activity: Dict[str, Any]) -> Dict[str, Any]:
    if "@context" in activity:
        del activity["@context"]
    return activity


def activity_from_doc(item: Dict[str, Any], embed: bool = False) -> Dict[str, Any]:
    item = add_extra_collection(item)
    activity = clean_activity(item)
    if embed:
        return remove_context(activity)
    return activity


def clean_activity(activity: ObjectType) -> Dict[str, Any]:
    """Clean the activity before rendering it.
     - Remove the hidden bco and bcc field
    """
    for field in ["bto", "bcc", "source"]:
        if field in activity:
            del (activity[field])
        if activity["type"] == "Create" and field in activity["object"]:
            del (activity["object"][field])
    return activity


def build_ordered_collection(items, actor_id, page, limit=50):
    total_items = len(items)

    if total_items <= 0:
        return {
            "@context": ap.COLLECTION_CTX,
            "id": f"{actor_id}/followers",
            "totalItems": 0,
            "type": ap.ActivityType.ORDERED_COLLECTION.value,
            "orderedItems": [],
        }

    if not page:
        resp = {
            "@context": ap.COLLECTION_CTX,
            "id": f"{actor_id}/followers",
            "totalItems": total_items,
            "type": ap.ActivityType.ORDERED_COLLECTION.value,
            "first": {
                "id": f"{actor_id}/followers?page=0",
                "orderedItems": [item.url for item in items],
                "partOf": f"{actor_id}/followers",
                "totalItems": total_items,
                "type": ap.ActivityType.ORDERED_COLLECTION_PAGE.value,
            },
        }
        if len(items) == limit:
            resp["first"]["next"] = f"{actor_id}/followers?page=1"

        return resp

    # return resp
