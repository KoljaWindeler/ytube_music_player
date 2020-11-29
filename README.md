# yTube Music Player

Adds a mediaplayer to Home Assistant that can stream tracks from a playlist to a media player.

**This component will set up the following platforms.**

Platform | Description
-- | --
`media_player` | will allow to play music from your YouTube Music account

![Example](screenshot.png)


## Features
- loads all your playlists from your YouTube Music account
- can either play straigt from the playlist or create a radio based on the playlist
- extracts url of the stream and forwards it to a generic mediaplayer
- keeps auto_playing as long as it is turned on

# Installation

## HACS

The easiest way to add this to your Homeassistant installation is using [HACS]. 

It's recommended to restart Homeassistent directly after the installation without any change to the Configuration. 
Homeassistent will install the dependencies during the next reboot. After that you can add and check the configuration without error messages. 
This is nothing special to this Integration but the same for all custom components.


## Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `kaco`.
4. Download _all_ the files from the `custom_components/ytube_music_player/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Follow the instructions under [Configuration](#Configuration) below.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/ytube_music_player/translations/en.json
custom_components/ytube_music_player/__init__.py
custom_components/ytube_music_player/manifest.json
custom_components/ytube_music_player/media_player.py
custom_components/ytube_music_player/config_flow.py
custom_components/ytube_music_player/const.py

```

# Setup

You need to grab and convert a cookie from youTube Music. This is described in https://ytmusicapi.readthedocs.io/en/latest/setup.html#copy-authentication-headers

**1. Basic steps for grabbing**
1. Open the development tools (I've used google chrome) [Crtl+Shift+I]
2. Open the Network tab
3. Open https://music.youtube.com, log out, log in
4. Search for "/browse" (for me only one item shows up) [If you can't find it: I had issues with ubuntu, worked instantly with windows]
5. Go to "headers" -> "request headers" and copy everything starting at "accept: */*" (mark with a mouse and copy to clipboard)

It should look like the screenshot below

![Cookie](cookie.png)

**2. The easiest way to prcocede is to convert is to use the config flow of homeassistant**
1. Open Settings -> Integrations -> "add integration" -> "YouTube Music Player"
2. Paste the cookie into the first field
3. Make sure that the path below is valid for your environment. Docker uses /config/, but ymmv.
4. Save, it will claim that it worked (hopefully) but you still have to add the configuration to you yaml! 
(full storage based configuration isn't working yet)


## Configuration options

Key | Type | Required | Default | Description
-- | -- | -- | -- | --
`header_pth` | `string` | `true` | `None` | The path of the header files from step 3 above
`speaker` | `string list` | `true` | `None` | List of speakers, see below in the example config

## Manual configuration 

Last step is simply the setup in yaml. 
All you have to do is to download the already existing package file download 
https://raw.githubusercontent.com/KoljaWindeler/ytube_music_player/main/package/ytube.yaml
into you /config/packages folder (see https://www.home-assistant.io/docs/configuration/packages/)

Or copy this into your configuration.yaml:
```yaml
media_player:
  - platform: ytube_music_player
    # adapt the file location if needed. this has to match the file path that was
    # speicified in the config flow
    header_path: '/config/headers_auth.json'
    speakers:
      # if your speaker is called media_player.speaker123, add speaker123 here
      - speaker123


input_select:
  ytube_music_player_source:
    name: Source
    icon: mdi:music-box-multiple
    options: # don't change
    - "Playlist Radio"
    - "Playlist"

  ytube_music_player_speakers:
    name: Speakers
    icon: mdi:speaker
    options: # don't change
    - "loading"

  ytube_music_player_playlist:
    name: Playlist
    icon: mdi:playlist-music
    options: # don't change
    - "loading"

  ytube_music_player_playmode:
    name: Playmode
    icon: mdi:playlist-music
    options: ## don't change
    - "Shuffle"
    - "Random"
    - "Shuffle Random"
    - "Direct"
```
## Credits
This is based on the gmusic mediaplayer of tprelog (https://github.com/tprelog/homeassistant-gmusic_player), ytmusicapi (https://github.com/sigma67/ytmusicapi) and ytube (https://github.com/nficano/pytube)
