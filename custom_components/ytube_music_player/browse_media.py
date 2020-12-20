"""Support for media browsing."""
import logging

from .const import *
from homeassistant.components.media_player import BrowseError, BrowseMedia


PLAYABLE_MEDIA_TYPES = [
    MEDIA_TYPE_ALBUM,
    MEDIA_TYPE_ARTIST,
    MEDIA_TYPE_TRACK,
    MEDIA_TYPE_PLAYLIST,
    LIB_TRACKS,
    HISTORY,
]

CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS = {
    MEDIA_TYPE_ALBUM: MEDIA_CLASS_ALBUM,
    LIB_ALBUM: MEDIA_CLASS_ALBUM,
    MEDIA_TYPE_ARTIST: MEDIA_CLASS_ARTIST,
    MEDIA_TYPE_PLAYLIST: MEDIA_CLASS_PLAYLIST,
    LIB_PLAYLIST: MEDIA_CLASS_PLAYLIST,
    HISTORY: MEDIA_CLASS_PLAYLIST,
    MEDIA_TYPE_SEASON: MEDIA_CLASS_SEASON,
    MEDIA_TYPE_TVSHOW: MEDIA_CLASS_TV_SHOW,
}

CHILD_TYPE_MEDIA_CLASS = {
    MEDIA_TYPE_SEASON: MEDIA_CLASS_SEASON,
    MEDIA_TYPE_ALBUM: MEDIA_CLASS_ALBUM,
    MEDIA_TYPE_ARTIST: MEDIA_CLASS_ARTIST,
    MEDIA_TYPE_MOVIE: MEDIA_CLASS_MOVIE,
    MEDIA_TYPE_PLAYLIST: MEDIA_CLASS_PLAYLIST,
    MEDIA_TYPE_TRACK: MEDIA_CLASS_TRACK,
    MEDIA_TYPE_TVSHOW: MEDIA_CLASS_TV_SHOW,
    MEDIA_TYPE_CHANNEL: MEDIA_CLASS_CHANNEL,
    MEDIA_TYPE_EPISODE: MEDIA_CLASS_EPISODE,
}

_LOGGER = logging.getLogger(__name__)

class UnknownMediaType(BrowseError):
    """Unknown media type."""


async def build_item_response(hass, media_library, payload):
    """Create response payload for the provided media query."""
    search_id = payload["search_id"]
    search_type = payload["search_type"]

    thumbnail = None
    title = None
    media = None
    
    if search_type == LIB_PLAYLIST:
        media = await hass.async_add_executor_job(media_library.get_library_playlists,BROWSER_LIMIT)
        title = "User Playlists"
    elif search_type == MEDIA_TYPE_PLAYLIST:
        res = await hass.async_add_executor_job(media_library.get_playlist,search_id, BROWSER_LIMIT)
        media = res['tracks']
        title = res['title']
    elif search_type == LIB_ALBUM:
        media = await hass.async_add_executor_job(media_library.get_library_albums, BROWSER_LIMIT)
        title = "User Albums"
    elif search_type == MEDIA_TYPE_ALBUM:
        res = await hass.async_add_executor_job(media_library.get_album,search_id)
        media = res['tracks']
        title = res['title']
    elif search_type == LIB_TRACKS:
        media = await hass.async_add_executor_job(media_library.get_library_songs)
        title = "User Songs"
    elif search_type == HISTORY:
        search_id = HISTORY
        title = "Last played songs"
        media = await hass.async_add_executor_job(media_library.get_history)

    if media is None:
        return None

    children = []
    for item in media:
        try:
            children.append(item_payload(item, media_library))
        except UnknownMediaType:
            pass


    response = BrowseMedia(
        media_class=CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS.get(
            search_type, MEDIA_CLASS_DIRECTORY
        ),
        media_content_id=search_id,
        media_content_type=search_type,
        title=title,
        can_play=search_type in PLAYABLE_MEDIA_TYPES and search_id,
        can_expand=True,
        children=children,
        thumbnail=thumbnail,
    )

    if search_type == "library_music":
        response.children_media_class = MEDIA_CLASS_MUSIC
    else:
        response.calculate_children_class()

    return response


def item_payload(item, media_library):
    """
    Create response payload for a single media item.

    Used by async_browse_media.
    """

    media_class = None
    title = ""
    media_content_type = None
    media_content_id = ""
    can_play = False
    can_expand = False
    thumbnail = ""

    if "playlistId" in item: #kolja
        title = f"{item['title']}"
        media_class = MEDIA_CLASS_PLAYLIST
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_PLAYLIST
        media_content_id = f"{item['playlistId']}"
        can_play = True
        can_expand = True
    elif "videoId" in item: #kolja
        title = f"{item['title']}"
        if(isinstance(item["artists"],str)):
            artist = item["artists"]
        elif(isinstance(item["artists"],list)):
            artist = item["artists"][0]["name"]
        else:
            artist = ""
        title = artist +" - "+title
        media_class = MEDIA_CLASS_TRACK
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_TRACK
        media_content_id = f"{item['videoId']}"
        can_play = True
        can_expand = False
    elif "browseId" in item: #kolja
        title = f"{item['title']}"
        media_class = MEDIA_CLASS_ALBUM
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_ALBUM
        media_content_id = f"{item['browseId']}"
        can_play = True
        can_expand = True

    
    else:
        # this case is for the top folder of each type
        # possible content types: album, artist, movie, library_music, tvshow, channel
        media_class = MEDIA_CLASS_DIRECTORY
        media_content_type = item["type"]
        media_content_id = ""
        can_play = False
        can_expand = True
        title = item["label"]

    if media_class is None:
        try:
            media_class = CHILD_TYPE_MEDIA_CLASS[media_content_type]
        except KeyError as err:
            _LOGGER.debug("Unknown media type received: %s", media_content_type)
            raise UnknownMediaType from err

    #_LOGGER.debug(title+' / '+media_class+' / '+media_content_id+' / '+media_content_type+' / '+str(can_play))

    return BrowseMedia(
        title=title,
        media_class=media_class,
        media_content_type=media_content_type,
        media_content_id=media_content_id,
        can_play=can_play,
        can_expand=can_expand,
        thumbnail=thumbnail,
    )


def library_payload(media_library):
    """
    Create response payload to describe contents of a specific library.

    Used by async_browse_media.
    """

    library_info = BrowseMedia(
        media_class=MEDIA_CLASS_DIRECTORY,
        media_content_id="library",
        media_content_type="library",
        title="Media Library",
        can_play=False,
        can_expand=True,
        children=[],
    )

    library = {
        LIB_PLAYLIST: "Playlists",
        LIB_ALBUM: "Albums",
        LIB_TRACKS: "Tracks",
        HISTORY: "History",
    }
    for item in [{"label": name, "type": type_} for type_, name in library.items()]:
        library_info.children.append(
            item_payload(
                {"label": item["label"], "type": item["type"], "uri": item["type"]},
                media_library,
            )
        )

    return library_info