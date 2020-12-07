It should be possible to use multipe accounts with the following steps:
1. Open Settings -> Integration -> Add new "YouTube Music Player" -> Paste cookie data of the first user
2. The integration will generate a ytube_header.json file in the .storage folder of your configuration, rename this file to something like ytube_header_kolja.json
3. Repeat Step 1 (you can delete the component before, or just have two of them)
4. Repeate Step 2
5. Define the media_player and all input selects twice (source / playlist / speaker / playmode) and directly link them directly as shown below.

## Player 1
```yaml
media_player:
    ############## Koljas Player ##############
  - platform: ytube_music_player
    header_path: '/config/.storage/ytube_header_kolja.json'
    speakers: 
      - keller_2
    select_source:   ytube_music_player_source_kolja
    select_playlist: ytube_music_player_playlist_kolja
    select_speakers: ytube_music_player_speakers_kolja
    select_playmode: ytube_music_player_playmode_kolja

input_select:
  ############################
  ### Koljas select fields ###
  ############################
    ytube_music_player_source_kolja:
        name: Source
        icon: mdi:music-box-multiple
        options:
        - "Playlist Radio"
        - "Playlist"

    ytube_music_player_speakers_kolja:
        name: Speakers
        icon: mdi:speaker
        options:  ## Should be empty
        - " "

    ytube_music_player_playlist_kolja:
        name: Playlist
        icon: mdi:playlist-music
        options: ## Should be empty
        - " "

    ytube_music_player_playmode_kolja:
        name: Playmode
        icon: mdi:playlist-music
        options: ## Should be empty
        - "Shuffle"
        - "Random"
        - "Shuffle Random"
        - "Direct"
    
  

```

## Input_select
```yaml
media_player:
    ############## Caros Player ##############
  - platform: ytube_music_player
    header_path: '/config/.storage/ytube_header_caro.json'
    speakers: 
      - keller
    select_source:   ytube_music_player_source_caro
    select_playlist: ytube_music_player_playlist_caro
    select_speakers: ytube_music_player_speakers_caro
    select_playmode: ytube_music_player_playmode_caro

input_select:
  ###########################  
  ### Caros select fields ###
  ###########################

    ytube_music_player_source_caro:
        name: Source
        icon: mdi:music-box-multiple
        options:
        - "Playlist Radio"
        - "Playlist"

    ytube_music_player_speakers_caro:
        name: Speakers
        icon: mdi:speaker
        options:  ## Should be empty
        - " "

    ytube_music_player_playlist_caro:
        name: Playlist
        icon: mdi:playlist-music
        options: ## Should be empty
        - " "

    ytube_music_player_playmode_caro:
        name: Playmode
        icon: mdi:playlist-music
        options: ## Should be empty
        - "Shuffle"
        - "Random"
        - "Shuffle Random"
        - "Direct"
 ```
