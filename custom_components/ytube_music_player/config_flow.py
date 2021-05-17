"""Provide the config flow."""
from homeassistant.core import callback
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging
from .const import *
import os.path
from homeassistant.helpers.storage import STORAGE_DIR
from ytmusicapi import YTMusic
import traceback
import asyncio
from collections import OrderedDict

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class yTubeMusicFlowHandler(config_entries.ConfigFlow):
	"""Provide the initial setup."""

	CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
	VERSION = 1

	def __init__(self):
		"""Provide the init function of the config flow."""
		# Called once the flow is started by the user
		self._errors = {}

	# will be called by sending the form, until configuration is done
	async def async_step_user(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		self._errors = {}
		if user_input is not None:
			# there is user input, check and save if valid (see const.py)
			self._errors = await async_check_data(self.hass,user_input)
			if self._errors == {}:
				self.data = user_input
				if(self.data[CONF_ADVANCE_CONFIG]):
					return await self.async_step_finish()
				else:
					return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
				#return await self.async_step_finish(user_input)
		# no user input, or error. Show form
		if(user_input==None):
			user_input = dict()
			user_input[CONF_HEADER_PATH] = os.path.join(self.hass.config.path(STORAGE_DIR),DEFAULT_HEADER_FILENAME)
			user_input[CONF_NAME] = DOMAIN

		return self.async_show_form(step_id="user", data_schema=vol.Schema(await async_create_form(self.hass,user_input,1)), errors=self._errors)

	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		self._errors = {}
		if user_input is not None:
			self.data.update(user_input)
			self._errors = await async_check_data(self.hass,user_input)
			if self._errors == {}:
				self.data.update(user_input)
				return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,2)), errors=self._errors)

	# TODO .. what is this good for?
	async def async_step_import(self, user_input):  # pylint: disable=unused-argument
		"""Import a config entry.

		Special type of import, we're not actually going to store any data.
		Instead, we're going to rely on the values that are in config file.
		"""
		if self._async_current_entries():
			return self.async_abort(reason="single_instance_allowed")

		return self.async_create_entry(title="configuration.yaml", data={})

	@staticmethod
	@callback
	def async_get_options_flow(config_entry):
		"""Call back to start the change flow."""
		return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
	"""Change an entity via GUI."""

	def __init__(self, config_entry):
		"""Set initial parameter to grab them later on."""
		# store old entry for later
		self.data = {}
		self.data.update(config_entry.data.items())

	# will be called by sending the form, until configuration is done
	async def async_step_init(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		self._errors = {}
		if user_input is not None:
			# there is user input, check and save if valid (see const.py)
			self._errors = await async_check_data(self.hass,user_input)
			if self._errors == {}:
				self.data.update(user_input)
				if(self.data[CONF_ADVANCE_CONFIG]):
					return await self.async_step_finish()
				else:
					return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
				#return await self.async_step_finish(user_input)
		elif self.data is not None:
			# if we came straight from init
			user_input = self.data
		# no user input, or error. Show form
		return self.async_show_form(step_id="init", data_schema=vol.Schema(await async_create_form(self.hass,user_input,1)), errors=self._errors)

	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		self._errors = {}
		if user_input is not None:
			self.data.update(user_input)
			self._errors = await async_check_data(self.hass,user_input)
			if self._errors == {}:
				self.data.update(user_input)
				return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
		elif self.data is not None:
			# if we came straight from init
			user_input = self.data
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,2)), errors=self._errors)


async def async_create_form(hass, user_input, page=1):
	"""Create form for UI setup."""
	user_input = ensure_config(user_input)
	data_schema = OrderedDict()

	all_media_player = dict()
	all_entities = await hass.async_add_executor_job(hass.states.all) 
	for e in all_entities:
		if(e.entity_id.startswith(DOMAIN_MP) and not(e.entity_id.startswith(DOMAIN_MP+"."+DOMAIN))):
			all_media_player.update({e.entity_id: e.entity_id.replace(DOMAIN_MP+".","")})
	

	if(page == 1):
		data_schema[vol.Required(CONF_NAME, default=user_input[CONF_NAME])] = str # name of the component without domain
		data_schema[vol.Required(CONF_COOKIE, default=user_input[CONF_COOKIE])] = str # configuration of the cookie
		data_schema[vol.Required(CONF_RECEIVERS,default=user_input[CONF_RECEIVERS])] = cv.multi_select(all_media_player)
		data_schema[vol.Required(CONF_HEADER_PATH, default=user_input[CONF_HEADER_PATH])] = str # file path of the header
		data_schema[vol.Required(CONF_ADVANCE_CONFIG, default=user_input[CONF_ADVANCE_CONFIG])] = vol.Coerce(bool) # show page 2

	elif(page == 2):
		data_schema[vol.Optional(CONF_SHUFFLE, default=user_input[CONF_SHUFFLE])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_LIKE_IN_NAME, default=user_input[CONF_LIKE_IN_NAME])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_DEBUG_AS_ERROR, default=user_input[CONF_DEBUG_AS_ERROR])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_LEGACY_RADIO, default=user_input[CONF_LEGACY_RADIO])] = vol.Coerce(bool) # default radio generation typ
		data_schema[vol.Optional(CONF_TRACK_LIMIT, default=user_input[CONF_TRACK_LIMIT])] = vol.Coerce(int)
		data_schema[vol.Optional(CONF_BRAND_ID, default=user_input[CONF_BRAND_ID])] = str # brand id
		data_schema[vol.Optional(CONF_SELECT_SPEAKERS, default=user_input[CONF_SELECT_SPEAKERS])] = str # drop down to select remote_player
		data_schema[vol.Optional(CONF_SELECT_SOURCE, default=user_input[CONF_SELECT_SOURCE])] = str # drop down to select playlist / playlist-radio
		data_schema[vol.Optional(CONF_SELECT_PLAYLIST, default=user_input[CONF_SELECT_PLAYLIST])] = str # drop down that holds the playlists
		data_schema[vol.Optional(CONF_SELECT_PLAYCONTINUOUS, default=user_input[CONF_SELECT_PLAYCONTINUOUS])] = str # select of input_boolean -> continuous on/off

		data_schema[vol.Optional(CONF_PROXY_PATH, default=user_input[CONF_PROXY_PATH])] = str # select of input_boolean -> continuous on/off
		data_schema[vol.Optional(CONF_PROXY_URL, default=user_input[CONF_PROXY_URL])] = str # select of input_boolean -> continuous on/off

	return data_schema


async def async_check_data(hass, user_input):
	"""Check validity of the provided date."""
	ret = {}
	if(CONF_COOKIE in user_input and CONF_HEADER_PATH in user_input):
		# sadly config flow will not allow to have a multiline text field
		# we get a looong string that we've to rearrange into multiline for ytmusic

		# the only thing we need is cookie + x-goog-authuser, lets try to cut this out
		# so the fields are written like 'identifier':'value', but some values actually have ':' inside, bummer.
		c = user_input[CONF_COOKIE]
		clean_cookie = ""
		clean_x_goog_authuser = ""
		## lets try to find the cookie part
		cookie_pos = c.lower().find('cookie')
		if(cookie_pos>=0):
			#_LOGGER.debug("found cookie in text")
			cookie_end = c[cookie_pos:]
			cookie_end_split = cookie_end.split(':')
			if(len(cookie_end_split)>=3):
				#_LOGGER.debug("found three or more sections")
				cookie_length_last_field = cookie_end_split[2].rfind(' ')
				if(cookie_length_last_field>=0):
					#_LOGGER.debug("found a space")
					cookie_length = len(cookie_end_split[0])+1+len(cookie_end_split[1])+1+cookie_length_last_field
					clean_cookie = c[cookie_pos:cookie_pos+cookie_length]
					#_LOGGER.debug(clean_cookie)
		## lets try to find x-auth-part
		xauth_pos = c.lower().find('x-goog-authuser: ')
		if(xauth_pos>=0):
			#_LOGGER.debug("found x-goog-authuser in text")
			#_LOGGER.debug(c[xauth_pos+len('x-goog-authuser: '):])
			xauth_len = c[xauth_pos+len('x-goog-authuser: '):].find(' ')
			#_LOGGER.debug(xauth_len)
			if(xauth_len>=0):
				#_LOGGER.debug("found space in text")
				clean_x_goog_authuser = c[xauth_pos:(xauth_pos+len('x-goog-authuser: ')+xauth_len)]
				#_LOGGER.debug(clean_x_goog_authuser)
		## lets see what we got
		if(clean_cookie!="" and clean_x_goog_authuser!=""):
			# woop woop, this COULD be it
			c = clean_cookie+"\n"+clean_x_goog_authuser+"\n"
		else:
			# well we've failed to find the cookie, the only thing we can do is at least to help with some breaks
			c = c.replace('cookie','\ncookie')
			c = c.replace('Cookie','\nCookie')
			c = c.replace('x-goog-authuser','\nx-goog-authuser')
			c = c.replace('X-Goog-AuthUser','\nX-Goog-AuthUser')
		#_LOGGER.debug("feeding with: ")
		#_LOGGER.debug(c)
		try:
			YTMusic.setup(filepath = user_input[CONF_HEADER_PATH], headers_raw = c)
		except:
			ret["base"] = ERROR_GENERIC
			formatted_lines = traceback.format_exc().splitlines()
			for i in formatted_lines:
				if(i.startswith('Exception: ')):
					if(i.find('The following entries are missing in your headers: Cookie')>=0):
						ret["base"] = ERROR_COOKIE
					elif(i.find('The following entries are missing in your headers: X-Goog-AuthUser')>=0):
						ret["base"] = ERROR_AUTH_USER
			_LOGGER.error(traceback.format_exc())
			return ret
		[ret, msg, api] = await async_try_login(hass,user_input[CONF_HEADER_PATH],"")
	return ret