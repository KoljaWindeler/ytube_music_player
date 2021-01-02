"""Support for media browsing."""
import logging

from .const import *
from homeassistant.components.media_player import BrowseError, BrowseMedia


PLAYABLE_MEDIA_TYPES = [
    MEDIA_TYPE_ALBUM,
    USER_ALBUM,
    MEDIA_TYPE_ARTIST,
    USER_ARTIST,
    MEDIA_TYPE_TRACK,
    MEDIA_TYPE_PLAYLIST,
    LIB_TRACKS,
    HISTORY,
    USER_TRACKS,
]

CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS = {
    MEDIA_TYPE_ALBUM: MEDIA_CLASS_ALBUM,
    LIB_ALBUM: MEDIA_CLASS_ALBUM,
    MEDIA_TYPE_ARTIST: MEDIA_CLASS_ARTIST,
    MEDIA_TYPE_PLAYLIST: MEDIA_CLASS_PLAYLIST,
    LIB_PLAYLIST: MEDIA_CLASS_PLAYLIST,
    HISTORY: MEDIA_CLASS_PLAYLIST,
    USER_TRACKS: MEDIA_CLASS_PLAYLIST,
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
    
    if search_type == LIB_PLAYLIST: # playlist OVERVIEW
        media = await hass.async_add_executor_job(media_library.get_library_playlists,BROWSER_LIMIT)
        title = "Library Playlists" # single playlist
    elif search_type == MEDIA_TYPE_PLAYLIST:
        res = await hass.async_add_executor_job(media_library.get_playlist,search_id, BROWSER_LIMIT)
        media = res['tracks']
        title = res['title']
    elif search_type == LIB_ALBUM: # album OVERVIEW
        media = await hass.async_add_executor_job(media_library.get_library_albums, BROWSER_LIMIT)
        title = "Library Albums"
    elif search_type == MEDIA_TYPE_ALBUM: # single album (NOT uploaded)
        res = await hass.async_add_executor_job(media_library.get_album,search_id)
        media = res['tracks']
        title = res['title']
    elif search_type == LIB_TRACKS: # liked songs (direct list, NOT uploaded)
        media = await hass.async_add_executor_job(media_library.get_library_songs)
        title = "Library Songs"
    elif search_type == HISTORY: # history songs (direct list)
        media = await hass.async_add_executor_job(media_library.get_history)
        search_id = HISTORY
        title = "Last played songs"
    elif search_type == USER_TRACKS: 
        media = await hass.async_add_executor_job(media_library.get_library_upload_songs,BROWSER_LIMIT)
        search_id = USER_TRACKS
        title = "Uploaded songs"
    elif search_type == USER_ALBUMS:
        media = await hass.async_add_executor_job(media_library.get_library_upload_albums,BROWSER_LIMIT)
        for i in media:
            i['type'] = USER_ALBUM
        title = "Uploaded Albums"
    elif search_type == USER_ALBUM:
        res = await hass.async_add_executor_job(media_library.get_library_upload_album,search_id)
        media = res['tracks']
        title = res['title']
    elif search_type == USER_ARTISTS:
        media = await hass.async_add_executor_job(media_library.get_library_upload_artists,BROWSER_LIMIT)
        title = "Uploaded Artists"
    elif search_type == USER_ARTIST:
        media = await hass.async_add_executor_job(media_library.get_library_upload_artist,search_id)
        title = "Uploaded Artist"
        if(isinstance(media,list)):
            if('artist' in media[0]):
                if(isinstance(media[0]['artist'],list)):
                    if('name' in media[0]['artist'][0]):
                        title = media[0]['artist'][0]['name']

    if media is None:
        return None

    children = []
    for item in media:
        try:
            children.append(item_payload(item, media_library,search_type))
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


def item_payload(item, media_library,search_type):
    """
    Create response payload for a single media item.

    Used by async_browse_media.
    """
    _LOGGER.debug('item_payload')
    #_LOGGER.debug(item)
    #_LOGGER.debug(search_type)


    media_class = None
    title = ""
    media_content_type = None
    media_content_id = ""
    can_play = False
    can_expand = False
    thumbnail = ""

    if "playlistId" in item: #playlist
        title = f"{item['title']}"
        media_class = MEDIA_CLASS_PLAYLIST
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_PLAYLIST
        media_content_id = f"{item['playlistId']}"
        can_play = True
        can_expand = True
    elif "videoId" in item: #tracks
        title = f"{item['title']}"
        if("artists" in item):
            artist = ""
            if(isinstance(item["artists"],str)):
                artist = item["artists"]
            elif(isinstance(item["artists"],list)):
                artist = item["artists"][0]["name"]
            if(artist):
                title = artist +" - "+title
        media_class = MEDIA_CLASS_TRACK
        if 'thumbnails' in item:
            if isinstance(item['thumbnails'],list):
                thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_TRACK
        media_content_id = f"{item['videoId']}"
        can_play = True
        can_expand = False
    elif search_type == USER_ARTISTS: # user uploaded artists overview
        title = f"{item['artist']}"
        media_class = MEDIA_CLASS_ARTIST
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = USER_ARTIST # send to single artist
        media_content_id = f"{item['browseId']}"
        can_play = True #?
        can_expand = True #?
    elif search_type in [USER_ALBUMS, LIB_ALBUM]:
        title = f"{item['title']}"
        media_class = MEDIA_CLASS_ALBUM
        thumbnail = item['thumbnails'][-1]['url']
        media_content_type = MEDIA_TYPE_ALBUM
        if search_type == USER_ALBUMS:
            media_content_type = USER_ALBUM
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
        USER_TRACKS: "Tracks uploaded",
        USER_ALBUMS: "Albums uploaded",
        USER_ARTISTS: "Artists uploaded",
    }
    for item in [{"label": name, "type": type_} for type_, name in library.items()]:
        library_info.children.append(
            item_payload(
                {"label": item["label"], "type": item["type"], "uri": item["type"]},
                media_library,
                None
            )
        )

    return library_info