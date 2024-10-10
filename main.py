import syncedlyrics
import requests
import asyncio
import time
import os
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as mc

class Discord: # https://gist.github.com/3kh0/b28f8e499ff2682e444e528d0e066a3e
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }

    def ChangeStatus(self, status, message):
        jsonData = {
            "status": status,
            "custom_status": {
                "text": message,
        }}
        r = requests.patch("https://discord.com/api/v8/users/@me/settings", headers=self.headers, json=jsonData)
        return r.status_code
async def Run(discord, status, lyrics):
    discord = discord
    status_code = discord.ChangeStatus(status, lyrics)
    if status_code == 200:
        print('changed status successfully')
    else:
        print("An error occured. Try again?")

async def get(): #get metadata info
	try:
		request = await mc.request_async()
		cs = request.get_current_session()
		mp = await cs.try_get_media_properties_async()
		author = mp.album_artist if not mp.album_artist == '' else mp.artist
		title = mp.album_title if not mp.album_title == '' else mp.title
		status = cs.get_playback_info().playback_status
		return author, title, status
	except Exception as e:
		print(f'ошибка при получении данных {e}')
		pass

async def main(token):
	info = await get()
	elapsed_formatted = '[00:00.00]'
	elapsed = float(0)
	current_track = f'{info[0]} - {info[1]}'
	previous_track = current_track
	current_time = time.time()
	current_line = None
	discord = Discord(token)
	lyrics = []
	print(f'searching lyrics for {current_track}')
	lrc = syncedlyrics.search(current_track, synced_only=True, providers=['Lrclib', 'NetEase', 'Megalobiz'])
	print(f'lyrics for {current_track} are {"found" if not lrc is None else "not found"}')
	while True:
		status = await get()
		current_track = f'{status[0]} - {status[1]}'

		match status[2]: #check music status
			case 4: #if music is playing
				lrc = None
				if elapsed > 10000: #i have no idea what i've done, but "it just works" (C)
					current_time = elapsed
				elapsed = time.time() - current_time

				mm = int(elapsed // 60)
				ss = int(elapsed % 60)
				ms = int((elapsed - int(elapsed)) * 100)
				elapsed_formatted = f"[{mm:02}:{ss:02}.{ms:02}]"

				if previous_track != current_track:
					os.system('cls')
					print(f'\nsearching lyrics for {current_track}')
					previous_track = current_track
					lyrics = []
					current_time = time.time()
					lrc = syncedlyrics.search(current_track, synced_only=True, providers=['Lrclib', 'NetEase', 'Megalobiz'])
					print(f'changed info, now its {current_track}, and lyrics are {"found" if not lrc is None else "not found"}')
				else:
					pass

				line = next((lyrics for time, lyrics in lyrics if time == elapsed_formatted[1:6]), None)
				if line:
					if current_line != line:
						current_line = line
						await Run(discord, "online", line[11:] if not line is None else '')
						print(line)

			case 5: #if music is paused
				current_time = elapsed
				pass

		if not lrc is None:
			for line in lrc.splitlines():
				lyrics.append((line[1:6], line))
		time.sleep(.1)

if __name__ == '__main__':
	if not os.path.exists('./tkn.txt'):
		token = input('Please, paste your Discord token. It will be saved in tkn.txt file.\n')
		with open('tkn.txt', 'w') as f:
			f.write(token)
	else:
		print('Token exists! If code always returns errors, try to check the token.')
		with open('tkn.txt', 'r') as f:
			token = f.read()
	asyncio.run(main(token))
