import requests
import re
from datetime import date
from pytube import YouTube
from pytube import request
from pytube import extract
from pytube.cipher import Cipher
from urllib.parse import unquote
from ytmusicapi import YTMusic

embed_url = "https://music.youtube.com"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
signatureTimestamp = 0 

def get_signatureTimestamp():
  signatureTimestamp=0
  embed_html = requests.get(embed_url, headers=headers)
  if(embed_html.status_code==200):
    s = str(embed_html.content)
    reg = re.search(r'"jsUrl":"(.*?)"', s)
    if(reg is not None):
      base_url = s[reg.span()[0]+9:reg.span()[1]-1]
      base_js = requests.get(embed_url+base_url, headers=headers)
      if(base_js.status_code==200):
        s=str(base_js.content)
        reg = re.search(r'signatureTimestamp:[0-9]+', s)
        if(reg is not None):
          signatureTimestamp = s[reg.span()[0]+19:reg.span()[1]]
          print('via lookup')
  if(signatureTimestamp==0):
    signatureTimestamp = (date.today() - date.fromtimestamp(0)).days - 1
    print('via date')
  return signatureTimestamp

def get_url(s):
  
  #s=ytmusic.get_song(videoId)['streamingData']['formats'][0]['signatureCipher']
  url = s[s.find('url=')+4:]
  sig = s[2:s.find('&')]

  url = (unquote(url))
  sig = (unquote(sig))

  embed_url = "https://www.youtube.com/embed/BB2mjBuAtiQ"
  embed_html = request.get(embed_url)
  js_url = extract.js_url(embed_html)
  _js = request.get(js_url)
  _cipher = Cipher(js=_js)

  signature = _cipher.get_signature(ciphered_signature=sig)
  return url+"&sig="+signature 


signatureTimestamp = get_signatureTimestamp()
ytmusic = YTMusic('/home/projects/homeassistant/.storage/ytube_header.json')

s=ytmusic.get_song('G1qPhcUgMDU',signatureTimestamp)['streamingData']

print(len(s['adaptiveFormats']))

s1=s['formats'][0]['signatureCipher']
url = get_url(s1)
print(url)
print("")

i=0

for a in s['adaptiveFormats']:
  print("stream "+str(i))
  i+=1
  url = get_url(a['signatureCipher'])
  print(url)
  print("")

