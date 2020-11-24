from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging
import datetime
from collections import OrderedDict
from ytmusicapi import YTMusic


from homeassistant.const import (
	EVENT_HOMEASSISTANT_START,
	ATTR_ENTITY_ID,
	CONF_DEVICE_ID,
	CONF_USERNAME,
	CONF_PASSWORD,
	STATE_PLAYING,
	STATE_PAUSED,
	STATE_OFF,
	STATE_IDLE,
)

from homeassistant.components.media_player import (
	MediaPlayerEntity,
	PLATFORM_SCHEMA,
	SERVICE_TURN_ON,
	SERVICE_TURN_OFF,
	SERVICE_PLAY_MEDIA,
	SERVICE_MEDIA_PAUSE,
	SERVICE_VOLUME_UP,
	SERVICE_VOLUME_DOWN,
	SERVICE_VOLUME_SET,
	ATTR_MEDIA_VOLUME_LEVEL,
	ATTR_MEDIA_CONTENT_ID,
	ATTR_MEDIA_CONTENT_TYPE,
	DOMAIN as DOMAIN_MP,
)

from homeassistant.components.media_player.const import (
	MEDIA_TYPE_MUSIC,
	SUPPORT_STOP,
	SUPPORT_PLAY,
	SUPPORT_PAUSE,
	SUPPORT_PLAY_MEDIA,
	SUPPORT_PREVIOUS_TRACK,
	SUPPORT_NEXT_TRACK,
	SUPPORT_VOLUME_MUTE,
 	SUPPORT_VOLUME_SET,
	SUPPORT_VOLUME_STEP,
	SUPPORT_TURN_ON,
	SUPPORT_TURN_OFF,
	SUPPORT_SHUFFLE_SET,
)

# Should be equal to the name of your component.
PLATFORM = "media_player"
DOMAIN = "ytube_music_player"
VERSION = "0.1.0"
ISSUE_URL = "https://github.com/koljawindeler/kaco/issues"

SUPPORT_YTUBEMUSIC_PLAYER = (
	SUPPORT_TURN_ON
	| SUPPORT_TURN_OFF
	| SUPPORT_PLAY
	| SUPPORT_PAUSE
	| SUPPORT_STOP
	| SUPPORT_VOLUME_SET
	| SUPPORT_VOLUME_STEP
	| SUPPORT_VOLUME_MUTE
	| SUPPORT_PREVIOUS_TRACK
	| SUPPORT_NEXT_TRACK
	| SUPPORT_SHUFFLE_SET
)

CONF_RECEIVERS = 'speakers'	 # list of speakers (media_players)
CONF_HEADER_PATH = 'header_path'
CONF_SHUFFLE = 'shuffle'
CONF_SHUFFLE_MODE = 'shuffle_mode'
CONF_COOKIE = 'cookie'

CONF_SELECT_SOURCE = 'select_source'
CONF_SELECT_PLAYLIST = 'select_playlist'
CONF_SELECT_SPEAKERS = 'select_speakers'

DEFAULT_SELECT_SOURCE = DOMAIN + '_source'
DEFAULT_SELECT_PLAYLIST = DOMAIN + '_playlist'
DEFAULT_SELECT_SPEAKERS = DOMAIN + '_speakers'
DEFAULT_HEADER_PATH = '/config/headers_auth.json'

DEFAULT_SHUFFLE_MODE = 1
DEFAULT_SHUFFLE = True

ERROR_COOKIE = 'error_cookie'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend = vol.Schema({
	DOMAIN: vol.Schema({
		vol.Optional(CONF_RECEIVERS): cv.string,
		vol.Optional(CONF_HEADER_PATH, default=DEFAULT_HEADER_PATH): cv.string,
		vol.Optional(CONF_SELECT_SOURCE, default=DEFAULT_SELECT_SOURCE): cv.string,
		vol.Optional(CONF_SELECT_PLAYLIST, default=DEFAULT_SELECT_PLAYLIST): cv.string,
		vol.Optional(CONF_SELECT_SPEAKERS, default=DEFAULT_SELECT_SPEAKERS): cv.string,
	})
}, extra=vol.ALLOW_EXTRA)

# Shortcut for the logger
_LOGGER = logging.getLogger(__name__)


def check_data(user_input):
	"""Check validity of the provided date."""
	ret = {}
	if(CONF_COOKIE in user_input) and (CONF_HEADER_PATH in user_input):
		try:
			# sadly config flow will not allow to have a multiline text field
			# we get a looong string that we've to rearrange into multiline for ytmusic
			c = user_input[CONF_COOKIE]
			c = c.replace('Cookie','\nCookie')
			c = c.replace('Accept-Encoding','\nAccept-Encoding')
			c = c.replace('Accept-Language','\nAccept-Language')
			c = c.replace('Authorization','\nAuthorization')
			c = c.replace('Host','\nHost')
			c = c.replace('User-Agent','\nUser-Agent')
			c = c.replace('X-Goog-AuthUser','\nX-Goog-AuthUser')
			c = c.replace('X-Goog-Visitor-Id','\nX-Goog-Visitor-Id')
			c = c.replace('x-origin','\nx-origin')
			c = c.replace('X-YouTube-Client-Name','\nX-YouTube-Client-Name')
			c = c.replace('X-Youtube-Identity-Token','\nX-Youtube-Identity-Token')
			c = c.replace('X-YouTube-Page-CL','\nX-YouTube-Page-CL')
			YTMusic.setup(filepath = user_input[CONF_HEADER_PATH], headers_raw = c)
			return {}
		except Exception:
			ret["base"] = ERROR_COOKIE
			return ret

def ensure_config(user_input):
	"""Make sure that needed Parameter exist and are filled with default if not."""
	out = {}
	out[CONF_HEADER_PATH] = DEFAULT_HEADER_PATH
#	out[CONF_ICON] = DEFAULT_ICON
	out[CONF_RECEIVERS] = ''
	out[CONF_SHUFFLE] = DEFAULT_SHUFFLE
	out[CONF_SHUFFLE_MODE] = DEFAULT_SHUFFLE_MODE
	out[CONF_SELECT_SOURCE] = DEFAULT_SELECT_SOURCE
	out[CONF_SELECT_PLAYLIST] = DEFAULT_SELECT_PLAYLIST
	out[CONF_SELECT_SPEAKERS] = DEFAULT_SELECT_SPEAKERS

	if user_input is not None:
		if CONF_HEADER_PATH in user_input:
			out[CONF_HEADER_PATH] = user_input[CONF_HEADER_PATH]
		if CONF_RECEIVERS in user_input:
			out[CONF_RECEIVERS] = user_input[CONF_RECEIVERS]
		if CONF_SHUFFLE in user_input:
			out[CONF_SHUFFLE] = user_input[CONF_SHUFFLE]
		if CONF_SHUFFLE_MODE in user_input:
			out[CONF_SHUFFLE_MODE] = user_input[CONF_SHUFFLE_MODE]
		if CONF_SELECT_SOURCE in user_input:
			out[CONF_SELECT_SOURCE] = user_input[CONF_SELECT_SOURCE]
		if CONF_SELECT_PLAYLIST in user_input:
			out[CONF_SELECT_PLAYLIST] = user_input[CONF_SELECT_PLAYLIST]
		if CONF_SELECT_SPEAKERS in user_input:
			out[CONF_SELECT_SPEAKERS] = user_input[CONF_SELECT_SPEAKERS]
	return out


def create_form(user_input):
	"""Create form for UI setup."""
	user_input = ensure_config(user_input)

	data_schema = OrderedDict()
	data_schema[vol.Required(CONF_COOKIE, default="")] = str
	data_schema[vol.Required(CONF_HEADER_PATH, default=user_input[CONF_HEADER_PATH])] = str
#	data_schema[vol.Required(CONF_RECEIVERS, default=user_input[CONF_RECEIVERS])] = str
#	data_schema[vol.Optional(CONF_SHUFFLE, default=user_input[CONF_SHUFFLE])] = vol.Coerce(bool)
#	data_schema[vol.Optional(CONF_SHUFFLE_MODE, default=user_input[CONF_SHUFFLE_MODE])] = vol.Coerce(int)
#	data_schema[vol.Optional(CONF_SELECT_SOURCE, default=user_input[CONF_SELECT_SOURCE])] = str
#	data_schema[vol.Optional(CONF_SELECT_PLAYLIST, default=user_input[CONF_SELECT_PLAYLIST])] = str
#	data_schema[vol.Optional(CONF_SELECT_SPEAKERS, default=user_input[CONF_SELECT_SPEAKERS])] = str

	return data_schema
