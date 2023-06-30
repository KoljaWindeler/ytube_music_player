"""HTTP API hooks for youtube music player."""

import logging
from typing import cast

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.network import get_url

from .const import DOMAIN, URL_PROXY_SHORT
from .media_player import yTubeMusicComponent


_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant) -> None:
	"""Handles setup for HTTP API endpoints."""
	hass.http.register_view(YTubeShortProxyView)

	hass.data.setdefault(DOMAIN, {})
	hass.data[DOMAIN]["short_proxy_url"] = await get_proxy_url(hass)

	_LOGGER.info("registered short proxy redirector")

class YTubeShortProxyView(HomeAssistantView):
	"""Simple view to handle searching for and sending a redirect for a URL."""
	name = "api:ytube:short-proxy"
	requires_auth = False
	url: str = URL_PROXY_SHORT

	async def get(self, request: web.Request, player_name: str, key: str) -> None:
		"""Handles the GET request to find a proxied URL."""
		hass: HomeAssistant = request.app["hass"]
		_LOGGER.debug("request for key %s for player %s", key, player_name)

		if key is None or player_name is None:
			_LOGGER.info("key or player not found. player: %s, key: %s", player_name, key)
			raise web.HTTPNotFound()

		mp = await get_music_player_instance(hass, player_name)
		if mp is None:
			_LOGGER.info("could not find matching media player: %s", player_name)
			raise web.HTTPNotFound()

		if not mp._proxy_redir:
			_LOGGER.info("proxy_redir not enabled for player %s", mp)
			raise web.HTTPBadRequest()

		url = mp._proxy_redir_dict.get(key)
		if url is None:
			raise web.HTTPNotFound()

		raise web.HTTPFound(url)

async def get_music_player_instance(hass: HomeAssistant, player_name: str) -> yTubeMusicComponent | None:
	"""Finds the requested music player instance in the ytube_music_player platform."""
	entities = entity_platform.async_get_platforms(hass, 'ytube_music_player')
	media_player_domain = [*filter(lambda e: e.domain == "media_player", entities)]
	if len(media_player_domain) != 1:
		_LOGGER.warning("found more than one domain in the ytube_music_player platform")
		return None

	media_players = cast(dict[str, yTubeMusicComponent], media_player_domain[0].entities)
	return media_players.get(player_name)

async def get_proxy_url(hass: HomeAssistant) -> str:
	"""Gets the full proxy url base used to send to music players."""
	url = get_url(hass)
	url += URL_PROXY_SHORT

	return url

# vim:sw=4:sts=4:ts=4:noet
