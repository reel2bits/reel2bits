from flask import url_for
from models import Album, Sound
import json


def to_json_relationship(of_user, against_user):
    """
    user relationship against_user
    of_user is the user "point of view"
    following = is of_user following against_user ?
    followed_by = is against_user following of_user ?
    etc.
    """
    if not of_user:
        return None
    obj = dict(
        id=against_user.id,
        following=True if of_user.actor[0].is_following(against_user.actor[0]) else False,
        followed_by=True if against_user.actor[0].is_following(of_user.actor[0]) else False,
        blocking=False,  # TODO handle that
        muting=False,  # TODO maybe handle that
        muting_notifications=False,
        requested=False,  # TODO handle that
        domain_blocking=False,
        showing_reblogs=True,
        endorsed=False,  # not managed
    )
    return obj


def to_json_account(user, relationship=False):
    obj = dict(
        id=user.id,
        username=user.name,
        acct=user.name,
        display_name=user.display_name,
        locked=False,
        created_at=user.created_at,
        followers_count=user.actor[0].followers.count(),
        following_count=user.actor[0].followings.count(),
        statuses_count=user.sounds.filter(
            Sound.private.is_(False), Sound.transcode_state == Sound.TRANSCODE_DONE
        ).count(),
        note=user.actor[0].summary,
        url=user.actor[0].url,
        avatar=("" or "/static/userpic_placeholder.svg"),
        avatar_static=("" or "/static/userpic_placeholder.svg"),
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
        reel2bits={
            "albums_count": user.albums.filter(Album.private.is_(False)).count(),
            "lang": user.locale,
            "quota_limit": user.quota,
            "quota_count": user.quota_count,
        },
    )
    if relationship:
        obj["pleroma"]["relationship"] = relationship
    return obj


def to_json_track(track, account):
    si = track.sound_infos.first()
    url_orig = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=True), _external=False)
    url_transcode = url_for("get_uploads_stuff", thing="sounds", stuff=track.path_sound(orig=False), _external=False)
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
            "type": "track",
            "slug": track.slug,
            "local": track.user.actor[0].is_local(),
            "title": track.title,
            "picture_url": None,  # FIXME not implemented yet
            "media_orig": url_orig,
            "media_transcoded": url_transcode,
            "waveform": (json.loads(si.waveform) if si else None),
            "private": track.private,
            "uploaded_elapsed": track.elapsed(),
            "album_id": (track.album.id if track.album else None),
            "album_order": (track.album_order if track.album else None),
            "processing": {
                "basic": (si.done_basic if si else None),
                "transcode_state": track.transcode_state,
                "transcode_needed": track.transcode_needed,
                "done": track.processing_done(),
            },
            "metadatas": {
                "licence": track.licence_info(),
                "duration": (si.duration if si else None),
                "type": (si.type if si else None),
                "codec": (si.codec if si else None),
                "format": (si.format if si else None),
                "channels": (si.channels if si else None),
                "rate": (si.rate if si else None),  # Hz
                "file_size": track.file_size,
                "transcode_file_size": track.transcode_file_size,
            },
        },
    }
    if si:
        if si.bitrate and si.bitrate_mode:
            obj["reel2bits"]["metadatas"]["bitrate"] = si.bitrate
            obj["reel2bits"]["metadatas"]["bitrate_mode"] = si.bitrate_mode
    return obj


def to_json_album(album, account):
    obj = {
        "id": album.flake_id,
        "uri": None,
        "url": None,
        "account": account,
        "in_reply_to_id": None,
        "in_reply_to_account_id": None,
        "reblog": None,
        "content": album.description,
        "created_at": album.created,
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
            "type": "album",
            "slug": album.slug,
            "local": True,  # NOTE, albums doesn't federate (yet)
            "title": album.title,
            "picture_url": None,  # FIXME not implemented yet
            "private": album.private,
            "uploaded_elapsed": album.elapsed(),
            "tracks_count": album.sounds.count(),
            "tracks": [to_json_track(t, account) for t in album.sounds],
        },
    }
    return obj


def default_genres():
    return [
        "acid house",
        "acid jazz",
        "acid techno",
        "acoustic blues",
        "acoustic rock",
        "afrobeat",
        "alternative country",
        "alternative dance",
        "alternative folk",
        "alternative hip hop",
        "alternative metal",
        "alternative pop",
        "alternative punk",
        "alternative rock",
        "ambient",
        "ambient house",
        "ambient techno",
        "americana",
        "anarcho-punk",
        "aor",
        "arena rock",
        "art rock",
        "atmospheric black metal",
        "audiobook",
        "avant-garde",
        "avant-garde jazz",
        "avant-garde metal",
        "avant-garde pop",
        "bachata",
        "ballad",
        "barbershop",
        "baroque",
        "bebop",
        "bhangra",
        "big band",
        "big beat",
        "black metal",
        "blackened death metal",
        "blackgaze",
        "blue-eyed soul",
        "bluegrass",
        "blues",
        "blues rock",
        "bolero",
        "bolero son",
        "boom bap",
        "bossa nova",
        "breakbeat",
        "breakcore",
        "breaks",
        "britpop",
        "broken beat",
        "brutal death metal",
        "bubblegum pop",
        "cajun",
        "calypso",
        "canterbury scene",
        "cantopop",
        "celtic",
        "celtic punk",
        "chamber pop",
        "champeta",
        "chanson",
        "chicago blues",
        "chillout",
        "chiptune",
        "christian rock",
        "christmas music",
        "city pop",
        "classic blues",
        "classic country",
        "classic jazz",
        "classic rock",
        "classical",
        "club",
        "comedy",
        "conscious hip hop",
        "contemporary christian",
        "contemporary classical",
        "contemporary folk",
        "contemporary gospel",
        "contemporary jazz",
        "contemporary r&b",
        "contra",
        "cool jazz",
        "country",
        "country blues",
        "country folk",
        "country pop",
        "country rock",
        "crossover prog",
        "crust punk",
        "cumbia",
        "d-beat",
        "dance",
        "dance-pop",
        "dance-punk",
        "dancehall",
        "dark ambient",
        "dark electro",
        "dark folk",
        "dark wave",
        "death metal",
        "death-doom metal",
        "deathcore",
        "deathgrind",
        "deathrock",
        "deep house",
        "delta blues",
        "desert rock",
        "digital hardcore",
        "disco",
        "doo-wop",
        "doom metal",
        "downtempo",
        "drill",
        "drone",
        "drum and bass",
        "dub",
        "dub techno",
        "dubstep",
        "dungeon synth",
        "east coast hip hop",
        "ebm",
        "electric blues",
        "electro",
        "electro house",
        "electro swing",
        "electro-funk",
        "electro-industrial",
        "electroclash",
        "electronic",
        "electronic rock",
        "electronica",
        "electronicore",
        "electropop",
        "electropunk",
        "emo",
        "emocore",
        "enka",
        "ethereal",
        "euro house",
        "eurodance",
        "europop",
        "experimental",
        "experimental rock",
        "fado",
        "filk",
        "flamenco",
        "folk",
        "folk metal",
        "folk pop",
        "folk punk",
        "folk rock",
        "freak folk",
        "free improvisation",
        "free jazz",
        "funk",
        "funk carioca",
        "funk metal",
        "funk rock",
        "funk soul",
        "funky house",
        "fusion",
        "future jazz",
        "futurepop",
        "g-funk",
        "gabber",
        "gangsta rap",
        "garage",
        "garage house",
        "garage punk",
        "garage rock",
        "glam",
        "glam metal",
        "glam rock",
        "glitch",
        "goa trance",
        "goregrind",
        "gospel",
        "gothic",
        "gothic metal",
        "gothic rock",
        "grebo",
        "grime",
        "grindcore",
        "groove metal",
        "grunge",
        "guaracha",
        "happy hardcore",
        "hard bop",
        "hard house",
        "hard rock",
        "hard trance",
        "hardcore punk",
        "hardcore techno",
        "hardstyle",
        "heavy metal",
        "hip hop",
        "honky tonk",
        "horror punk",
        "horrorcore",
        "house",
        "idm",
        "illbient",
        "indie",
        "indie folk",
        "indie pop",
        "indie rock",
        "indietronica",
        "indorock",
        "industrial",
        "industrial metal",
        "industrial rock",
        "instrumental",
        "instrumental jazz",
        "instrumental rock",
        "irish folk",
        "italo-disco",
        "j-pop",
        "j-rock",
        "jazz",
        "jazz blues",
        "jazz fusion",
        "jazz rap",
        "jazz rock",
        "jazz-funk",
        "jungle",
        "k-pop",
        "kayōkyoku",
        "kizomba",
        "klezmer",
        "krautrock",
        "latin",
        "latin jazz",
        "latin pop",
        "latin rock",
        "leftfield",
        "line dance",
        "lo-fi",
        "lounge",
        "lovers rock",
        "madchester",
        "mainstream rock",
        "mambo",
        "mandopop",
        "martial industrial",
        "math rock",
        "mathcore",
        "medieval",
        "melodic black metal",
        "melodic death metal",
        "melodic metalcore",
        "melodic rock",
        "melodic trance",
        "mento",
        "merengue",
        "metal",
        "metalcore",
        "microhouse",
        "milonga",
        "min'yō",
        "mincecore",
        "minimal",
        "modern blues",
        "modern classical",
        "modern country",
        "motown",
        "mpb",
        "musical",
        "neo soul",
        "neo-progressive rock",
        "neo-rockabilly",
        "neofolk",
        "nerdcore",
        "new age",
        "new jack swing",
        "new romantic",
        "new wave",
        "no wave",
        "noise",
        "noise pop",
        "noisecore",
        "non-music",
        "norteño",
        "northern soul",
        "nu jazz",
        "nu metal",
        "occult rock",
        "oi",
        "old school death metal",
        "old-time",
        "opera",
        "orchestral",
        "outlaw country",
        "p-funk",
        "pachanga",
        "pop",
        "pop metal",
        "pop punk",
        "pop rap",
        "pop rock",
        "pop soul",
        "pornogrind",
        "post-bop",
        "post-classical",
        "post-grunge",
        "post-hardcore",
        "post-metal",
        "post-punk",
        "post-rock",
        "power electronics",
        "power metal",
        "power pop",
        "powerviolence",
        "production music",
        "progressive",
        "progressive folk",
        "progressive house",
        "progressive metal",
        "progressive rock",
        "progressive trance",
        "psy-trance",
        "psychedelic",
        "psychedelic folk",
        "psychedelic pop",
        "psychedelic rock",
        "psychobilly",
        "psytrance",
        "punk",
        "punk rock",
        "queercore",
        "r&b",
        "ragga",
        "ragga hip-hop",
        "ragga jungle",
        "ragtime",
        "raï",
        "ranchera",
        "rap rock",
        "rapcore",
        "rave",
        "reggae",
        "reggaeton",
        "rhythmic noise",
        "rock",
        "rock and roll",
        "rockabilly",
        "rocksteady",
        "roots reggae",
        "rumba",
        "salsa",
        "samba",
        "schlager",
        "screamo",
        "shibuya-kei",
        "shoegaze",
        "singer-songwriter",
        "ska",
        "ska punk",
        "skacore",
        "slow waltz",
        "sludge metal",
        "smooth jazz",
        "smooth soul",
        "soca",
        "soft rock",
        "son cubano",
        "son montuno",
        "soul",
        "soul jazz",
        "southern rock",
        "southern soul",
        "space rock",
        "speed garage",
        "speed metal",
        "spoken word",
        "stoner metal",
        "stoner rock",
        "street punk",
        "surf rock",
        "swing",
        "symphonic black metal",
        "symphonic metal",
        "symphonic prog",
        "symphonic rock",
        "symphony",
        "synth-pop",
        "synthwave",
        "tango",
        "tech house",
        "technical death metal",
        "techno",
        "teen pop",
        "thrash metal",
        "thrashcore",
        "timba",
        "traditional country",
        "trance",
        "trap",
        "trap edm",
        "tribal house",
        "trip hop",
        "turntablism",
        "uk drill",
        "uk garage",
        "underground hip hop",
        "vallenato",
        "vaporwave",
        "viking metal",
        "visual kei",
        "vocal house",
        "vocal jazz",
        "vocal trance",
        "west coast hip hop",
        "west coast swing",
        "yé-yé",
        "zamrock",
        "zydeco",
    ]
