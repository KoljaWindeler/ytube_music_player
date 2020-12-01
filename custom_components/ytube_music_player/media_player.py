"""
Attempting to support yTube Music in Home Assistant
"""
import asyncio
import logging
import time
import random
import pickle
import os.path
import random
import datetime
from urllib.parse import unquote

from .const import *
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.condition import state
from homeassistant.helpers.event import track_state_change
from homeassistant.helpers.event import call_later
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers import device_registry

import homeassistant.components.input_select as input_select

from pytube import YouTube
from pytube import request
from pytube import extract
from pytube.cipher import Cipher
from ytmusicapi import YTMusic



_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
	"""Run setup via YAML."""
	_LOGGER.debug("Config via YAML")
	if(config is not None):
		add_entities([yTubeMusicComponent(hass, config)], True)

async def async_setup_entry(hass, config, async_add_devices):
	"""Run setup via Storage."""
	_LOGGER.debug("Config via Storage/UI currently not supported due to me not understanding asyncio")
#	if(len(config.data) > 0):
#		async_add_devices([yTubeMusicComponent(hass, config.data)], True)


class yTubeMusicComponent(MediaPlayerEntity):
	def __init__(self, hass, config):
		self.hass = hass
		self._name = DOMAIN
		self._playlist = "input_select." + config.get(CONF_SELECT_PLAYLIST, DEFAULT_SELECT_PLAYLIST)
		self._playMode = "input_select." + config.get(CONF_SELECT_PLAYMODE, DEFAULT_SELECT_PLAYMODE)
		self._media_player = "input_select." + config.get(CONF_SELECT_SPEAKERS, DEFAULT_SELECT_SPEAKERS)
		self._source = "input_select." + config.get(CONF_SELECT_SOURCE, DEFAULT_SELECT_SOURCE)
		self._speakersList = config.get(CONF_RECEIVERS)

		default_header_file = os.path.join(hass.config.path(STORAGE_DIR),DEFAULT_HEADER_FILENAME)

		_LOGGER.debug("YtubeMediaPlayer config: ")
		_LOGGER.debug("\tHeader path: " + config.get(CONF_HEADER_PATH, default_header_file))
		_LOGGER.debug("\tplaylist: " + self._playlist)
		_LOGGER.debug("\tmediaplayer: " + self._media_player)
		_LOGGER.debug("\tsource: " + self._source)
		_LOGGER.debug("\tspeakerlist: " + str(self._speakersList))
		_LOGGER.debug("\tplayModes: " + str(self._playMode))


		if(os.path.exists(config.get(CONF_HEADER_PATH, default_header_file))):
			self._api = YTMusic(config.get(CONF_HEADER_PATH, default_header_file))
		else:
			msg= "can't file header file at "+config.get(CONF_HEADER_PATH, default_header_file)
			_LOGGER.error(msg)
			data = {"title": "yTubeMediaPlayer error", "message": msg}
			self.hass.services.call("persistent_notification","create", data)
			self._api = None

		self._js = ""
		self._get_cipher('BB2mjBuAtiQ')
#		embed_url = f"https://www.youtube.com/embed/D7oPc6PNCZ0"

		self._entity_ids = []  ## media_players - aka speakers
		self._playlists = []
		self._playlist_to_index = {}
		self._tracks = []
		self._track = []
		self._attributes = {}
		self._next_track_no = 0
		self._allow_next = False
		self._last_auto_advance = datetime.datetime.now()

		hass.bus.listen_once(EVENT_HOMEASSISTANT_START, self._update_sources)
		hass.bus.listen_once(EVENT_HOMEASSISTANT_START, self._get_speakers)
		hass.bus.listen('ytubemusic_player.sync_media', self._update_sources)
		hass.bus.listen('ytubemusic_player.play_media', self._ytubemusic_play_media)

		self._shuffle = config.get(CONF_SHUFFLE, DEFAULT_SHUFFLE)
		self._shuffle_mode = config.get(CONF_SHUFFLE_MODE, DEFAULT_SHUFFLE_MODE)

		self._playing = False
		self._state = STATE_OFF
		self._volume = 0.0
		self._is_mute = False
		self._track_name = None
		self._track_artist = None
		self._track_album_name = None
		self._track_album_cover = None
		self._track_artist_cover = None
		self._attributes['_player_state'] = STATE_OFF

#		asyncio.run_coroutine_threadsafe(self.test(), hass.loop)

#	async def test(self):
#		self._reg = await device_registry.async_get_registry(self.hass)
#		reg = self._reg._data_to_save()
#		for dev in reg.devices:
#
#		_LOGGER.error("called get registry")

	@property
	def name(self):
		""" Return the name of the player. """
		return self._name

	@property
	def icon(self):
		return 'mdi:music-circle'

	@property
	def supported_features(self):
		""" Flag media player features that are supported. """
		return SUPPORT_YTUBEMUSIC_PLAYER

	@property
	def should_poll(self):
		""" No polling needed. """
		return False

	@property
	def state(self):
		""" Return the state of the device. """
		return self._state

	@property
	def device_state_attributes(self):
		""" Return the device state attributes. """
		return self._attributes

	@property
	def is_volume_muted(self):
		""" Return True if device is muted """
		return self._is_mute

	@property
	def is_on(self):
		""" Return True if device is on. """
		return self._playing

	@property
	def media_content_type(self):
		""" Content type of current playing media. """
		return MEDIA_TYPE_MUSIC

	@property
	def media_title(self):
		""" Title of current playing media. """
		return self._track_name

	@property
	def media_artist(self):
		""" Artist of current playing media """
		return self._track_artist

	@property
	def media_album_name(self):
		""" Album name of current playing media """
		return self._track_album_name

	@property
	def media_image_url(self):
		""" Image url of current playing media. """
		return self._track_album_cover

	@property
	def media_image_remotely_accessible(self):
		# True  returns: entity_picture: http://lh3.googleusercontent.com/Ndilu...
		# False returns: entity_picture: /api/media_player_proxy/media_player.gmusic_player?token=4454...
		return True

	@property
	def shuffle(self):
		""" Boolean if shuffling is enabled. """
		return self._shuffle

	@property
	def volume_level(self):
	  """ Volume level of the media player (0..1). """
	  return self._volume


	def turn_on(self, *args, **kwargs):
		""" Turn on the selected media_player from input_select """
		if(self._api == None):
			_LOGGER.error("Can't start the player, no header file")
			return
		_LOGGER.debug("TURNON")

		self._playing = False
		if not self._update_entity_ids():
			return
		_player = self.hass.states.get(self._entity_ids)
		data = {ATTR_ENTITY_ID: _player.entity_id}

		self._allow_next = False
		track_state_change(self.hass, _player.entity_id, self._sync_player)
		track_state_change(self.hass, self._playMode, self._update_playmode)
		self._turn_on_media_player(data)
		#_LOGGER.error("subscribe to changes of ")

		self._get_cipher('BB2mjBuAtiQ')

		# display imidiatly a loading state to provide feedback to the user
		self._track_name =  "loading..."
		self._track_album_name = ""
		self._track_artist =  ""
		self._track_artist_cover =  None
		self._track_album_cover = None
		self._state = STATE_PLAYING # a bit early otherwise no info will be shown
		self.schedule_update_ha_state()

		# grabbing data from API, might take a 1-3 sec
		self._load_playlist()

	def _turn_on_media_player(self, data=None):
		"""Fire the on action."""
		if data is None:
			data = {ATTR_ENTITY_ID: self._entity_ids}
		self._state = STATE_IDLE
		self.schedule_update_ha_state()
		self.hass.services.call(DOMAIN_MP, 'turn_on', data)


	def turn_off(self, entity_id=None, old_state=None, new_state=None, **kwargs):
		""" Turn off the selected media_player """
		self._playing = False
		self._track_name = None
		self._track_artist = None
		self._track_album_name = None
		self._track_album_cover = None

		_player = self.hass.states.get(self._entity_ids)
		data = {ATTR_ENTITY_ID: _player.entity_id}
		self._turn_off_media_player(data)

	def _turn_off_media_player(self, data=None):
		"""Fire the off action."""
		self._playing = False
		self._state = STATE_OFF
		self._attributes['_player_state'] = STATE_OFF
		self.schedule_update_ha_state()
		if data is None:
			data = {ATTR_ENTITY_ID: self._entity_ids}
		self.hass.services.call(DOMAIN_MP, 'turn_off', data)


	def _update_entity_ids(self):
		""" sets the current media_player from input_select """
		media_player = self.hass.states.get(self._media_player) # Example: self.hass.states.get(input_select.gmusic_player_speakers)
		if media_player is None:
			_LOGGER.error("(%s) is not a valid input_select entity.", self._media_player)
			return False
		_entity_ids = "media_player." + media_player.state
		if self.hass.states.get(_entity_ids) is None:
			_LOGGER.error("(%s) is not a valid media player.", media_player.state)
			return False
		# Example: self._entity_ids = media_player.bedroom_stereo
		self._entity_ids = _entity_ids
		return True

	def _get_cipher(self, videoId):
		embed_url = "https://www.youtube.com/embed/"+videoId
		embed_html = request.get(url=embed_url)
		js_url = extract.js_url(embed_html)
		self._js = request.get(js_url)
		self._cipher = Cipher(js=self._js)
		#2do some sort of check if tis worked


	def _sync_player(self, entity_id=None, old_state=None, new_state=None):
		""" Perform actions based on the state of the selected (Speakers) media_player """
		if not self._playing:
			return
		""" _player = The selected speakers """
		_player = self.hass.states.get(self._entity_ids)

		#""" Entire state of the _player, include attributes. """
		# self._attributes['_player'] = _player

		""" entity_id of selected speakers. """
		self._attributes['_player_id'] = _player.entity_id

		""" _player state - Example [playing -or- idle]. """
		self._attributes['_player_state'] = _player.state

		#_LOGGER.error("State change of ")
		#_LOGGER.error(self._entity_ids)
		#_LOGGER.error(" to ")
		#_LOGGER.error(_player.state)
		#try:
		#	_LOGGER.error(_player.attributes['media_position'])
		#except:
		#	pass

		if 'media_position' in _player.attributes:
			if _player.state == 'playing' and _player.attributes['media_position']>0:
				self._allow_next = True
		if _player.state == 'idle':
			if self._allow_next:
				if (datetime.datetime.now()-self._last_auto_advance).total_seconds() > 10:
					self._allow_next = False
					self._last_auto_advance = datetime.datetime.now()
					self._get_track()
		elif _player.state == 'off':
			self._state = STATE_OFF
			self.turn_off()

		""" Set new volume if it has been changed on the _player """
		if 'volume_level' in _player.attributes:
			self._volume = round(_player.attributes['volume_level'],2)
		self.schedule_update_ha_state()

	def _ytubemusic_play_media(self, event):

		_speak = event.data.get('speakers')
		_source = event.data.get('source')
		_media = event.data.get('name')

		if event.data['shuffle_mode']:
			self._shuffle_mode = event.data.get('shuffle_mode')
			_LOGGER.info("SHUFFLE_MODE: %s", self._shuffle_mode)

		if event.data['shuffle']:
			self.set_shuffle(event.data.get('shuffle'))
			_LOGGER.info("SHUFFLE: %s", self._shuffle)

		_LOGGER.debug("YTUBEMUSIC PLAY MEDIA")
		_LOGGER.debug("Speakers: (%s) | Source: (%s) | Name: (%s)", _speak, _source, _media)
		self.play_media(_source, _media, _speak)

	def _update_sources(self, now=None):
		_LOGGER.debug("Load source lists")
		self._update_playlists()
		#self._update_library()
		#self._update_songs()

	def _get_speakers(self, now=None):
		data = {"options": list(self._speakersList), "entity_id": self._media_player}
		self.hass.services.call(input_select.DOMAIN, input_select.SERVICE_SET_OPTIONS, data)

	def _update_playlists(self, now=None):
		""" Sync playlists from Google Music library """
		if(self._api == None):
			return
		self._playlist_to_index = {}
		self._playlists = self._api.get_library_playlists(limit = 99)
		idx = -1
		for playlist in self._playlists:
			idx = idx + 1
			name = playlist.get('title','')
			if len(name) < 1:
				continue
			self._playlist_to_index[name] = idx
			#  the "your likes" playlist won't return a count of tracks
			if not('count' in playlist):
				extra_info = self._api.get_playlist(playlistId=playlist['playlistId'])
				self._playlists[idx]['count'] = int(extra_info['duration'].replace(' songs','').replace(',','').replace('.',''))

		playlists = list(self._playlist_to_index.keys())
		self._attributes['playlists'] = playlists

		data = {"options": list(playlists), "entity_id": self._playlist}
		self.hass.services.call(input_select.DOMAIN, input_select.SERVICE_SET_OPTIONS, data)


	def _load_playlist(self, playlist=None, play=True):
		_LOGGER.info("Reloading Playlist!")
		""" Load selected playlist to the track_queue """
		if not self._update_entity_ids():
			return
		""" if source == Playlist """
		_playlist_id = self.hass.states.get(self._playlist)
		if _playlist_id is None:
			_LOGGER.error("(%s) is not a valid input_select entity.", self._playlist)
			return
		if playlist is None:
			playlist = _playlist_id.state
		idx = self._playlist_to_index.get(playlist)
		if idx is None:
			_LOGGER.error("playlist to index is none!")
			self._turn_off_media_player()
			return
		self._tracks = None

		_source = self.hass.states.get(self._source)
		if _source is None:
			_LOGGER.error("(%s) is not a valid input_select entity.", self._source)
			return

		my_radio = self._api.get_playlist(playlistId = self._playlists[idx]['playlistId'], limit = int(self._playlists[idx]['count']))['tracks']
		#my_radio = self._api.get_watch_playlist(playlistId = self._playlists[idx]['playlistId'])#, limit = int(self._playlists[idx]['count']))
		if _source.state != 'Playlist':
			r_track = my_radio[random.randrange(0,len(my_radio)-1)]
			self._tracks = self._api.get_watch_playlist(videoId=r_track['videoId'])
		else:
			self._tracks = my_radio
		_LOGGER.debug("New Track database loaded, contains "+str(len(self._tracks))+" Tracks")

		self._total_tracks = len(self._tracks)
		#self.log("Loading [{}] Tracks From: {}".format(len(self._tracks), _playlist_id))

		# get current playmode
		self._update_playmode()

		if self._shuffle and self._shuffle_mode != 2:
			random.shuffle(self._tracks)
		if play:
			self._play()

	# called from HA when th user changes the input entry, will read selection to membervar
	def _update_playmode(self, entity_id=None, old_state=None, new_state=None):
		_LOGGER.debug("running update playmode")
		if(entity_id == None):
			_playmode = self.hass.states.get(self._playMode)
		else:
			_playmode = self.hass.states.get(entity_id)
		if _playmode != None:
			if(_playmode.state == "Shuffle"):
				self._shuffle = True
				self._shuffle_mode = 1
			elif(_playmode.state == "Random"):
				self._shuffle = True
				self._shuffle_mode = 2
			if(_playmode.state == "Shuffle Random"):
				self._shuffle = True
				self._shuffle_mode = 3
			if(_playmode.state == "Direct"):
				self._shuffle = False
				self._shuffle_mode = 0
		self.set_shuffle(self._shuffle)
		# if we've change the dropdown, reload the playlist and start playing
		# else only change the mode
		if(old_state != None and new_state != None):
			self._allow_next = False # player will change to idle, avoid auto_advance
			self._load_playlist(play = True)


	def _play(self):
		self._playing = True
		self._next_track_no = -1
		self._get_track()

	def _get_track(self, entity_id=None, old_state=None, new_state=None, retry=3):
		""" Get a track and play it from the track_queue. """
		_LOGGER.info(" NEXT TRACK ")

		""" grab next track from prefetched list """
		_track = None
		if self._shuffle and self._shuffle_mode != 1:
			self._next_track_no = random.randrange(self._total_tracks) - 1
		else:
			self._next_track_no = self._next_track_no + 1
			if self._next_track_no >= self._total_tracks:
				# we've reached the end of the playlist
				# reset the inner playlist counter, call _update_playlist to update lib
				self._next_track_no = 0
				self._load_playlist(play=False)
		try:
			_track = self._tracks[self._next_track_no]
		except IndexError:
			_LOGGER.error("Out of range! Number of tracks in track_queue == (%s)", self._total_tracks)
			self._turn_off_media_player()
			return
		if _track is None:
			_LOGGER.error("_track is None!")
			self._turn_off_media_player()
			return

		""" Find the unique track id. """
		uid = ''
		if 'videoId' in _track:
			uid = _track['videoId']
		else:
			_LOGGER.error("Failed to get ID for track: (%s)", _track)
			_LOGGER.error(_track)
			if retry < 1:
				self._turn_off_media_player()
				return
			return self._get_track(retry=retry-1)

		""" If available, get track information. """
		self._track_album_name = None
		self._track_artist_cover = None
		self._track_name = None
		self._track_artist = None
		self._track_album_cover = None
		if 'title' in _track:
			self._track_name = _track['title']
		if 'byline' in _track:
			self._track_artist = _track['byline']
		elif 'artists' in _track:
			self._track_artist = _track['artists'][0]['name']
		if 'thumbnail' in _track:
			_album_art_ref = _track['thumbnail']   ## returns a list,
			# thumbnail [0] is super tiny 32x32? / thumbnail [1] is ok-ish / thumbnail [2] is quite nice quality
			self._track_album_cover = _album_art_ref[len(_album_art_ref)-1]['url']
		elif 'thumbnails' in _track:
			_album_art_ref = _track['thumbnails']   ## returns a list
			self._track_album_cover = _album_art_ref[len(_album_art_ref)-1]['url']
		self.schedule_update_ha_state()

		"""@@@ Get the stream URL and play on media_player @@@"""
		_url = ''
		try:
			_LOGGER.debug("-- try to find streaming url --")
			streamingData=self._api.get_song(_track['videoId'])['streamingData']
			if('adaptiveFormats' in streamingData):
				streamingData = streamingData['adaptiveFormats']
			elif('formats' in streamingData): #backup, not sure if that is ever needed, or if adaptiveFormats are always present
				streamingData = streamingData['formats']
			streamId = 0
			# try to find audio only stream
			for i in range(0,len(streamingData)):
				if(streamingData[i]['mimeType'].startswith('audio/mp4')):
					streamId = i
					break
				elif(streamingData[i]['mimeType'].startswith('audio')):
					streamId = i
			sigCipher_ch = streamingData[streamId]['signatureCipher']
			sigCipher_ex = sigCipher_ch.split('&')
			res = dict({'s': '', 'url': ''})
			for sig in sigCipher_ex:
				for key in res:
					if(sig.find(key+"=")>=0):
						res[key]=unquote(sig[len(key+"="):])
			# I'm just not sure if the original video from the init will stay online forever
			# in case it's down the player might not load and thus we won't have a javascript loaded
			# so if that happens: we try with this url, might work better (at least the file should be online)
			# the only trouble i could see is that this video is private and thus also won't load the player .. 
			if(self._js == ""):
				self._get_cipher(_track['videoId'])
			signature = self._cipher.get_signature(ciphered_signature=res['s'])
			_url = res['url'] + "&sig=" + signature

		except Exception as err:
			_LOGGER.error("Failed to get own(!) URL for track, further details below. Will not try YouTube method")
			_LOGGER.error(traceback.format_exc())
			_LOGGER.error(_track['videoId'])
			_LOGGER.error(self._api.get_song(_track['videoId']))

		# backup: run youtube stack, only if we failed
		if(_url == ""):
			try:
				streams = YouTube('https://www.youtube.com/watch?v='+_track['videoId']).streams
				streams_audio = streams.filter(only_audio=True)
				if(len(streams_audio)):
					_url = streams_audio.order_by('abr').last().url
				else:
					_url = streams.order_by('abr').last().url
				_LOGGER.error("ultimatly")
				_LOGGER.error(_url)

			except Exception as err:
				_LOGGER.error(traceback.format_exc())
				_LOGGER.error("Failed to get URL for track: (%s)", uid)
				_LOGGER.error(err)
				if retry < 1:
					self._turn_off_media_player()
					return
				else:
					_LOGGER.error("Retry with: (%i)", retry)
				return self._get_track(retry=retry-1)

		self._state = STATE_PLAYING
		self.schedule_update_ha_state()
		data = {
			ATTR_MEDIA_CONTENT_ID: _url,
			ATTR_MEDIA_CONTENT_TYPE: "audio/mp3",
			ATTR_ENTITY_ID: self._entity_ids
			}
		self.hass.services.call(DOMAIN_MP, SERVICE_PLAY_MEDIA, data)


		"""@@@ Get the stream URL and play on media_player @@@"""
		#_LOGGER.error("register call later")
		# just to make sure that we check the status of the media player to free the "go to next"
		call_later(self.hass, 15, self._sync_player)


	def play_media(self, media_type, media_id, _player=None, **kwargs):
		if not self._update_entity_ids():
			return

		# Should skip this if input_select does not exist
		if _player is not None:
			_option = {"option": _player, "entity_id": self._media_player}
			self.hass.services.call(input_select.DOMAIN, input_select.SERVICE_SELECT_OPTION, _option)

		_source = {"option":"Playlist", "entity_id": self._source}
		_option = {"option": media_id, "entity_id": self._playlist}
		self.hass.services.call(input_select.DOMAIN, input_select.SERVICE_SELECT_OPTION, _source)
		self.hass.services.call(input_select.DOMAIN, input_select.SERVICE_SELECT_OPTION, _option)

		_player = self.hass.states.get(self._entity_ids)

		if self._playing == True:
			self.media_stop()
			self.media_play()
		elif self._playing == False and self._state == STATE_OFF:
			if _player.state == STATE_OFF:
				self.turn_on()
			else:
				data = {ATTR_ENTITY_ID: _player.entity_id}
				self._turn_off_media_player(data)
				call_later(self.hass, 1, self.turn_on)
		else:
			_LOGGER.error("self._state is: (%s).", self._state)

	def media_play(self, entity_id=None, old_state=None, new_state=None, **kwargs):
		"""Send play command."""
		if self._state == STATE_PAUSED:
			self._state = STATE_PLAYING
			self.schedule_update_ha_state()
			data = {ATTR_ENTITY_ID: self._entity_ids}
			self.hass.services.call(DOMAIN_MP, 'media_play', data)
		else:
			_source = self.hass.states.get(self._source)
			source = _source.state
			self._load_playlist()

	def media_pause(self, **kwargs):
		""" Send media pause command to media player """
		self._state = STATE_PAUSED
		#_LOGGER.error(" PAUSE ")
		self.schedule_update_ha_state()
		data = {ATTR_ENTITY_ID: self._entity_ids}
		self.hass.services.call(DOMAIN_MP, 'media_pause', data)

	def media_play_pause(self, **kwargs):
		"""Simulate play pause media player."""
		if self._state == STATE_PLAYING:
			self._allow_next = False
			self.media_pause()
		else:
			self._allow_next = False
			self.media_play()

	def media_previous_track(self, **kwargs):
		"""Send the previous track command."""
		if self._playing:
			self._next_track_no = max(self._next_track_no - 2, -1)
			self._allow_next = False
			self._get_track()

	def media_next_track(self, **kwargs):
		"""Send next track command."""
		if self._playing:
			self._allow_next = False
			self._get_track()

	def media_stop(self, **kwargs):
		"""Send stop command."""
		self._state = STATE_IDLE
		self._playing = False
		self._track_artist = None
		self._track_album_name = None
		self._track_name = None
		self._track_album_cover = None
		self.schedule_update_ha_state()
		data = {ATTR_ENTITY_ID: self._entity_ids}
		self.hass.services.call(DOMAIN_MP, 'media_stop', data)

	def set_shuffle(self, shuffle):
		self._shuffle = shuffle
		if self._shuffle_mode == 1:
			self._attributes['shuffle_mode'] = 'Shuffle'
		elif self._shuffle_mode == 2:
			self._attributes['shuffle_mode'] = 'Random'
		elif self._shuffle_mode == 3:
			self._attributes['shuffle_mode'] = 'Shuffle Random'
		else:
			self._attributes['shuffle_mode'] = self._shuffle_mode
		return self.schedule_update_ha_state()

	def set_volume_level(self, volume):
		"""Set volume level."""
		self._volume = round(volume,2)
		data = {ATTR_ENTITY_ID: self._entity_ids, 'volume_level': self._volume}
		self.hass.services.call(DOMAIN_MP, 'volume_set', data)
		self.schedule_update_ha_state()

	def volume_up(self, **kwargs):
		"""Volume up the media player."""
		newvolume = min(self._volume + 0.05, 1)
		self.set_volume_level(newvolume)

	def volume_down(self, **kwargs):
		"""Volume down media player."""
		newvolume = max(self._volume - 0.05, 0.01)
		self.set_volume_level(newvolume)

	def mute_volume(self, mute):
		"""Send mute command."""
		if self._is_mute == False:
			self._is_mute = True
		else:
			self._is_mute = False
		self.schedule_update_ha_state()
		data = {ATTR_ENTITY_ID: self._entity_ids, "is_volume_muted": self._is_mute}
		self.hass.services.call(DOMAIN_MP, 'volume_mute', data)
