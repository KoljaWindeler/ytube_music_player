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


async def build_item_response(hass, media_library, payload, search=None):
    """Create response payload for the provided media query."""
    search_id = payload[SEARCH_ID]
    search_type = payload[SEARCH_TYPE]

    children = []
    thumbnail = None
    title = None
    media = None
    p1 = datetime.datetime.now()
    _LOGGER.debug("- build_item_response for: "+search_type)
    
    if search_type == LIB_PLAYLIST: # playlist OVERVIEW -> lists playlists
        media = await hass.async_add_executor_job(media_library.get_library_playlists,BROWSER_LIMIT)
        title = LIB_PLAYLIST_TITLE # single playlist

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_PLAYLIST,
                media_content_type = MEDIA_TYPE_PLAYLIST,
                media_content_id = f"{item['playlistId']}",
                can_play = True,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))
        

    elif search_type == MEDIA_TYPE_PLAYLIST: # single playlist -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_playlist,search_id, BROWSER_LIMIT)
        title = media['title']

        for item in media['tracks']:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"],str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"],list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist +" - "+item_title
            
            thumbnail = ''
            if 'thumbnails' in item:
                if isinstance(item['thumbnails'],list):
                    thumbnail = item['thumbnails'][-1]['url']

            children.append(BrowseMedia(
                title = item_title,
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = thumbnail,
            ))
        
    elif search_type == LIB_ALBUM: # LIB! album OVERVIEW, not uploaded -> lists albums
        media = await hass.async_add_executor_job(media_library.get_library_albums, BROWSER_LIMIT)
        title = LIB_ALBUM_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_ALBUM,
                media_content_type = MEDIA_TYPE_ALBUM,
                media_content_id = f"{item['browseId']}",
                can_play = True,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == MEDIA_TYPE_ALBUM: # single album (NOT uploaded) -> lists tracks
        res = await hass.async_add_executor_job(media_library.get_album,search_id)
        media = res['tracks']
        title = res['title']
        
        for item in media:
            thumbnail = item['thumbnails'][-1]['url'] # here to expose it also for the header
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = True,
                thumbnail = thumbnail,
            ))

    elif search_type == LIB_TRACKS: # liked songs (direct list, NOT uploaded) -> lists tracks
        media = await hass.async_add_executor_job(lambda: media_library.get_library_songs(limit=BROWSER_LIMIT))
        title = LIB_TRACKS_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"],str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"],list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist +" - "+item_title

            children.append(BrowseMedia(
                title = item_title,
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == HISTORY: # history songs (direct list) -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_history)
        search_id = HISTORY
        title = HISTORY_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"],str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"],list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist +" - "+item_title

            children.append(BrowseMedia(
                title = item_title,
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_TRACKS:  # list all uploaded songs -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_library_upload_songs,BROWSER_LIMIT)
        search_id = USER_TRACKS
        title = USER_TRACKS_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artist" in item):
                artist = ""
                if(isinstance(item["artist"],str)):
                    artist = item["artist"]
                elif(isinstance(item["artist"],list)):
                    artist = item["artist"][0]["name"]
                if(artist):
                    item_title = artist +" - "+item_title

            children.append(BrowseMedia(
                title = item_title,
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_ALBUMS: # uploaded album overview!! -> lists user albums
        media = await hass.async_add_executor_job(media_library.get_library_upload_albums,BROWSER_LIMIT)
        title = USER_ALBUMS_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_ALBUM,
                media_content_type = USER_ALBUM,
                media_content_id = f"{item['browseId']}",
                can_play = True,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_ALBUM: # single uploaded album -> lists tracks
        res = await hass.async_add_executor_job(media_library.get_library_upload_album,search_id)
        media = res['tracks']
        title = res['title']

        for item in media:
            try:
                thumbnail = item['thumbnails'][-1]['url']
            except:
                thumbnail = ""

            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = thumbnail,
            ))

    elif search_type == USER_ARTISTS: # with S
        media = await hass.async_add_executor_job(media_library.get_library_upload_artists,BROWSER_LIMIT)
        title = USER_ARTISTS_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['artist']}",
                media_class = MEDIA_CLASS_ARTIST,
                media_content_type = USER_ARTIST,
                media_content_id = f"{item['browseId']}",
                can_play = False,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_ARTISTS_2: # list all artists now, but follow up will be the albums of that artist
        media = await hass.async_add_executor_job(media_library.get_library_upload_artists,BROWSER_LIMIT)
        title = USER_ARTISTS_2_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['artist']}",
                media_class = MEDIA_CLASS_ARTIST,
                media_content_type = USER_ARTIST_2,
                media_content_id = f"{item['browseId']}",
                can_play = False,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_ARTIST: # without S
        media = await hass.async_add_executor_job(media_library.get_library_upload_artist, search_id, BROWSER_LIMIT)
        title = USER_ARTIST_TITLE
        if(isinstance(media,list)):
            if('artist' in media[0]):
                if(isinstance(media[0]['artist'],list)):
                    if('name' in media[0]['artist'][0]):
                        title = media[0]['artist'][0]['name']

        for item in media:
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"],str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"],list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    title = artist +" - "+title

            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_TRACK,
                media_content_type = MEDIA_TYPE_TRACK,
                media_content_id = f"{item['videoId']}",
                can_play = True,
                can_expand = False,
                thumbnail = item['thumbnails'][-1]['url'],
            ))

    elif search_type == USER_ARTIST_2: # list each album of an uploaded artists only once .. next will be uploaded album view 'USER_ALBUM'
        media_all = await hass.async_add_executor_job(media_library.get_library_upload_artist, search_id, BROWSER_LIMIT)
        title = USER_ARTIST_2_TITLE
        media = list()
        for item in media_all:
            if('album' in item):
                if('name' in item['album']):
                    if(all(item['album']['name'] != a['title'] for a in media)):
                        media.append({
                            'type': 'user_album',
                            'browseId': item['album']['id'],
                            'title': item['album']['name'],
                            'thumbnails': item['thumbnails']
                        })
        if('artist' in media_all[0]):
                if(isinstance(media_all[0]['artist'],list)):
                    if('name' in media_all[0]['artist'][0]):
                        title = "Uploaded albums of "+media_all[0]['artist'][0]['name']
        

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_ALBUM,
                media_content_type = USER_ALBUM,
                media_content_id = f"{item['browseId']}",
                can_play = True,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))        


    elif search_type == SEARCH:
        title = SEARCH_TITLE
        #_LOGGER.debug("search entry")
        #_LOGGER.debug(search.get('filter',None))
        #_LOGGER.debug(search.get('limit',None))
        if search is not None:
            media_all = await hass.async_add_executor_job(lambda: media_library.search(query=search.get('query',""), filter=search.get('filter',None), limit=int(search.get('limit',20))))

            if(search.get('filter',None) is not None):
                helper = {}
            else:
                helper = {'song':"Track: ", 'playlist': "Playlist: ",'album':"Album: "}

            for a in media_all:
                if(a['resultType'] == 'song'):
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'],"")+a['title'],
                        media_class = MEDIA_CLASS_TRACK,
                        media_content_type = MEDIA_TYPE_TRACK,
                        media_content_id = a['videoId'],
                        can_play = True,
                        can_expand = False,
                        thumbnail = a['thumbnails'][-1]['url'],
                    ))
                elif(a['resultType'] == 'playlist'):
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'],"")+a['title'],
                        media_class = MEDIA_CLASS_PLAYLIST,
                        media_content_type = MEDIA_TYPE_PLAYLIST,
                        media_content_id = f"{a['browseId']}",
                        can_play = True,
                        can_expand = True,
                        thumbnail = a['thumbnails'][-1]['url'],
                    ))
                elif(a['resultType'] == 'album'):
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'],"")+a['title'],
                        media_class = MEDIA_CLASS_ALBUM,
                        media_content_type = MEDIA_TYPE_ALBUM,
                        media_content_id = f"{a['browseId']}",
                        can_play = True,
                        can_expand = True,
                        thumbnail = a['thumbnails'][-1]['url'],
                    ))
                else: # video / artists / uploads are currently ignored
                    continue

        #_LOGGER.debug("search entry end")
    elif search_type == MOOD_OVERVIEW:
        media_all = await hass.async_add_executor_job(lambda: media_library.get_mood_categories())
        title = MOOD_TITLE
        for cap in media_all:
            for e in media_all[cap]:
                children.append(BrowseMedia(
                    title = cap+' - '+e['title'],
                    media_class = MEDIA_CLASS_PLAYLIST,
                    media_content_type = MOOD_PLAYLISTS,
                    media_content_id = e['params'],
                    can_play = False,
                    can_expand = True,
                    thumbnail = "",
                ))
    elif search_type == MOOD_PLAYLISTS:
        media = await hass.async_add_executor_job(lambda: media_library.get_mood_playlists(search_id))
        title = MOOD_TITLE
        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",
                media_class = MEDIA_CLASS_PLAYLIST,
                media_content_type = MEDIA_TYPE_PLAYLIST,
                media_content_id = f"{item['playlistId']}",
                can_play = True,
                can_expand = True,
                thumbnail = item['thumbnails'][-1]['url'],
            ))


    ############################################ END ###############

    children.sort(key=lambda x: x.title, reverse=False)
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
    t = (datetime.datetime.now() - p1).total_seconds()
    _LOGGER.debug("- Calc / grab time: "+str(t)+" sec")
    return response



def library_payload(media_library,search=None):
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
        LIB_PLAYLIST: [LIB_PLAYLIST_TITLE,MEDIA_CLASS_PLAYLIST],
        LIB_ALBUM: [LIB_ALBUM_TITLE,MEDIA_CLASS_ALBUM],
        LIB_TRACKS: [LIB_TRACKS_TITLE, MEDIA_CLASS_TRACK],
        HISTORY: [HISTORY_TITLE, MEDIA_CLASS_TRACK],
        USER_TRACKS: [USER_TRACKS_TITLE, MEDIA_CLASS_TRACK],
        USER_ALBUMS: [USER_ALBUMS_TITLE, MEDIA_CLASS_ALBUM],
        USER_ARTISTS: [USER_ARTISTS_TITLE, MEDIA_CLASS_ARTIST],
        USER_ARTISTS_2: [USER_ARTISTS_2_TITLE, MEDIA_CLASS_ARTIST],
        MOOD_OVERVIEW: [MOOD_TITLE, MEDIA_CLASS_PLAYLIST]
    }
    if(search!=None):
        library.update({SEARCH: ["Results for \""+str(search.get("query","No search"))+"\"", MEDIA_CLASS_DIRECTORY]})
    
    for item in [{"label": extra[0], "type": type_, "class": extra[1]} for type_, extra in library.items()]:
        library_info.children.append(
            BrowseMedia(
                title=item["label"],
                media_class=item["class"],
                media_content_type=item["type"],
                media_content_id="",
                can_play=False,
                can_expand=True,
                thumbnail="",
            )
        )

    return library_info
