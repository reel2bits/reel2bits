from flask import url_for
import json
from models import licences as track_licenses


def to_json_account(user):
    return dict(
        id=user.id,
        username=user.name,
        acct=user.name,
        display_name=user.display_name,
        locked=False,
        created_at=user.created_at,
        followers_count=len(user.actor[0].followers),
        following_count=len(user.actor[0].followings),
        statuses_count=user.sounds.count(),
        note=user.actor[0].summary,
        url=user.actor[0].url,
        avatar="",
        avatar_static="",
        header="",
        header_static="",
        emojis=[],
        moved=None,
        fields=[],
        bot=False,
        source={
            "privacy": "unlisted",
            "sensitive": False,
            "language": user.locale,
            "note": user.actor[0].summary,
            "fields": [],
        },
        pleroma={"is_admin": user.is_admin()},
        reel2bits={"albums_count": user.albums.count()}
    )


def to_json_statuses(track, account):
    si = track.sound_infos.first()
    url_orig = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=True), _external=True)
    url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=True)
    obj = {
        "id": track.flake_id,
        "uri": None,
        "url": None,
        "account": account,
        "in_reply_to_id": None,
        "in_reply_to_account_id": None,
        "reblog": None,
        "content": track.description,
        "created_at": track.uploaded,
        "emojis": [],
        "replies_count": 0,
        "reblogs_count": 0,
        "favourites_count": 0,
        "reblogged": None,
        "favorited": None,
        "muted": None,
        "sensitive": None,
        "spoiler_text": None,
        "visibility": None,
        "media_attachment": [],
        "mentions": [],
        "tags": [],
        "card": None,
        "application": None,
        "language": None,
        "pinned": None,
        "reel2bits": {
            "local": track.user.actor[0].is_local(),
            "title": track.title,
            "picture_url": None,  # FIXME not implemented yet
            "media_orig": url_orig,
            "media_transcoded": url_transcode,
            "waveform": (json.loads(si.waveform) if si else None),
            "private": track.private,
            "uploaded_elapsed": track.elapsed(),
            "album_id": (track.album.flake_id if track.album else None),
            "processing": {
                "basic": (si.done_basic if si else None),
                "transcode_state": track.transcode_state,
                "transcode_needed": track.transcode_needed,
                "done": track.processing_done(),
            },
            "metadatas": {
                "licence": track_licenses[track.licence],
                "duration": (si.duration if si else None),
                "type": (si.type if si else None),
                "codec": (si.codec if si else None),
                "format": (si.format if si else None),
                "channels": (si.channels if si else None),
                "rate": (si.rate if si else None),  # Hz
            },
        },
    }
    if si:
        if si.bitrate and si.bitrate_mode:
            obj["reel2bits"]["metadatas"]["bitrate"] = si.bitrate
            obj["reel2bits"]["metadatas"]["bitrate_mode"] = si.bitrate_mode
    return obj
