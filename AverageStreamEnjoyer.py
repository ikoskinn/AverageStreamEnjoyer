#!/usr/bin/env python
# -*- coding: utf8 -*-

import asyncio
import os
import random
import re
import subprocess
import time
import urllib
from bs4 import BeautifulSoup

import simpleobsws
from twitchio.ext import commands
import configparser
import pyttsx3
import requests

config = configparser.ConfigParser() # INI
engine = pyttsx3.init() # TTS

class Bot(commands.Bot):
    def __init__(self):
        # Инициализируем INI настройки.
        config.read("settings.ini", encoding="latin-1")

        self.RootPath = os.path.abspath(os.curdir)

        # Список наград за баллы и их Reward ID.
        self.RewardIds = {
            'tts_speak': config['TTS']['rewardid'],
            'tts_change_nickname': config['TTS']['changepronunciationrewardid'],
            'send_pic': config['SendImage']['rewardid'],
            'play_sound': config['PlaySound']['rewardid']
        }

        # Параметры пользователя.
        self.InitialChannel = config['Main']['initialchannel'].lower()
        self.TwitchToken = config['Main']['twitchtoken'].lower()

        self.WS_Host = config['Websocket']['host']
        self.WS_Password = config['Websocket']['password']
        self.ImageBordersSourceName = config['Websocket']['imageborderssourcename']

        self.TTS_Enabled = config['TTS']['enabled'] == "True"
        self.TTS_ChangePronunciationEnabled = config['TTS']['changepronunciationenabled'] == "True"
        self.TTS_VoiceMessagesAdressedToAuthorOnly = config['TTS']['voicemessagesadressedtoauthoronly'] == "True"

        self.PlaySound_Enabled = config['PlaySound']['enabled'] == "True"
        self.PlaySound_Volume = int(config['PlaySound']['volume'])
        self.PlaySound_Timeout = int(config['PlaySound']['timeout'])

        self.SendImage_Enabled = config['SendImage']['enabled'] == "True"
        try:
            self.SendImage_Duracy = int(config['SendImage']['duracy'])
        except:
            self.SendImage_Duracy = -1

        self.WhiteList_Enabled = config['WhiteList']['enabled'] == "True"
        self.WhiteList_VipsAllowed = config['WhiteList']['vipsallowed'] == "True"
        self.WhiteList_ModsAllowed = config['WhiteList']['modsallowed'] == "True"
        self.WhiteList_ModsCanAdd = config['WhiteList']['modscanadd'] == "True"


        # Инициализируем Twitch-бота и OBS-бота.
        super().__init__(token=self.TwitchToken, prefix='!', initial_channels=[self.InitialChannel])
        self.ws = simpleobsws.WebSocketClient(url=self.WS_Host, password=self.WS_Password,
                                              identification_parameters=simpleobsws.IdentificationParameters(
                                                  ignoreNonFatalRequestChecks=False)
                                              )

        # Скорость озвучки TTS в миллисекундах.
        engine.setProperty('rate', 250)

    async def event_ready(self):
        # Вошли в аккаунт и готовы к работе.
        print(f'Вошли как | {self.nick}')
        print(f'ID пользователя: | {self.user_id}')

    async def RewardsHandle(self, message):
        # Обработчик наград за баллы канала.
        wl = False
        if self.TTS_ChangePronunciationEnabled is True and message.tags['custom-reward-id'] == self.RewardIds['Смена ника']:
            self.save_config('Names', message.author.name, message.content)
        elif self.SendImage_Enabled is True and message.tags['custom-reward-id'] == self.RewardIds['Отправить картинку']:
            if self.WhiteList_Enabled is True:
                if message.author.name in config['WhiteListUsers'].keys():
                    if config['WhiteListUsers'][message.author.name] == '1':
                        wl = True
            else:
                if self.TTS_VoiceMessagesAdressedToAuthorOnly is True:
                    if f'@{self.nick}' in message.content:
                        wl = True
                else:
                    wl = True

            try:
                if self.WhiteList_ModsAllowed is True and message.author.is_mod is True:
                    wl = True
                elif self.WhiteList_VipsAllowed is True and message.tags['vip'] == '1':
                    wl = True
            except:
                pass

            if wl is True:
                if '.jpg' in message.content or '.png' in message.content or '.gif' in message.content or '.jpeg' in message.content:
                    url = str(message.content).split('?')[0]
                    filename = str(url).split('/')[-1]
                    url = str(str(url).encode('utf-8')).replace('b', '').replace('\'', '')
                    r = requests.get(url)
                    with open(f"{self.RootPath}\\images\\" + filename, 'wb') as outfile:
                        outfile.write(r.content)

                    await self.set_twitch_pic(f"{self.RootPath}\\images\\" + filename, self.SendImage_Enabled)
            else:
                pass
        elif self.PlaySound_Enabled is True and message.tags['custom-reward-id'] == self.RewardIds['Проиграть звук']:
            if self.WhiteList_Enabled is True:
                if message.author.name in config['WhiteListUsers'].keys():
                    if config['WhiteListUsers'][message.author.name] == '1':
                        wl = True
            else:
                if self.TTS_VoiceMessagesAdressedToAuthorOnly is True:
                    if f'@{self.nick}' in message.content:
                        wl = True
                else:
                    wl = True

            try:
                if self.WhiteList_ModsAllowed is True and message.author.is_mod is True:
                    wl = True
                elif self.WhiteList_VipsAllowed is True and message.tags['vip'] == '1':
                    wl = True
            except:
                pass

            if wl is True:
                linkorname = message.content
                if 'http' not in linkorname:
                    query_string = urllib.parse.urlencode({"search_query": linkorname})
                    formatUrl = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)

                    search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode())
                    clip = requests.get("https://www.youtube.com/watch?v=" + "{}".format(search_results[0]))
                    clip2 = "https://www.youtube.com/watch?v=" + "{}".format(search_results[0])

                    inspect = BeautifulSoup(clip.content, "html.parser")
                    yt_title = inspect.find_all("meta", property="og:title")

                    test = f"{self.RootPath}\\mpv.exe --window-minimized=yes --no-video --volume {self.PlaySound_Volume}" + f" {clip2}"
                else:
                    test = f"{self.RootPath}\\mpv.exe --window-minimized=yes --no-video --volume {self.PlaySound_Volume}" + f" {linkorname}"

                p = subprocess.Popen(test)

                if self.SendImage_Duracy != -1:
                    await asyncio.sleep(self.SendImage_Duracy)
                    p.kill()

    async def event_message(self, message):
        if message.echo:
            return
        try:
            customRewardId = message.tags['custom-reward-id']
        except:
            customRewardId = ''

        if customRewardId != '':
            await self.RewardsHandle(message)
        else:
            if self.TTS_Enabled is True:
                name = message.author.name
                if name in config['Names'].keys():
                    name = config['Names'][name]

                if message.author.name != "streamelements" \
                and message.author.name != "moobot"\
                and '!sr' not in message.content\
                and 'https://' not in message.content:
                    if self.TTS_VoiceMessagesAdressedToAuthorOnly is True and len(self.RewardIds['Чтение сообщения']) < 5:
                        engine.say(f'{name} сказал {message.content}')
                        engine.runAndWait()

        print(f'{message.author.name}:' + message.content)

        await self.handle_commands(message)

    async def set_twitch_pic(self, pic, duracy=5):
        ws = self.ws

        await ws.connect()  # Make the connection to obs-websocket
        await ws.wait_until_identified()  # Wait for the identification handshake to complete

        requests = []

        # Получаем активную сцену чтобы создать картинку именно там.
        # Getting active scene to create an image exactly there.
        request = simpleobsws.Request('GetCurrentProgramScene')
        ret = await ws.call(request)

        currentSceneName = ret.responseData['currentProgramSceneName']
        sourceName = str(time.time())

        # Получаем ID источника с границами картинок.
        # Getting source ID with borders of pictures
        request = simpleobsws.Request('GetSceneItemId',
                                      {'sceneName': currentSceneName, 'sourceName': 'pic_borders'})
        ret = await ws.call(request)

        # Получаем границы где можно показать картинку
        # Getting borders where it possible to show pic
        request = simpleobsws.Request('GetSceneItemTransform',
                                      {'sceneName': currentSceneName, 'sceneItemId': ret.responseData['sceneItemId']})
        ret = await ws.call(request)

        borderX = ret.responseData['sceneItemTransform']['positionX']
        borderY = ret.responseData['sceneItemTransform']['positionY']
        borderW = ret.responseData['sceneItemTransform']['width']
        borderH = ret.responseData['sceneItemTransform']['height']

        # Создаем источник выключенным по умолч.
        # Creating disabled source by default
        request = simpleobsws.Request('CreateInput', {'sceneName': currentSceneName, 'inputName': sourceName,
                                                      'inputKind': 'image_source', 'inputSettings': {
                'file': pic},
                                                      'sceneItemEnabled': False})
        ret = await ws.call(request)

        sourceId = int(ret.responseData['sceneItemId'])

        # Меняем Opacity на 0.0 чтобы картинка сначала не появлялась.
        # Changing opacity of source to 0.0 so that the image doesnt appear.
        request = simpleobsws.Request('CreateSourceFilter',
                                      {'sourceName': sourceName, 'filterName': 'alpha', 'filterKind': 'color_filter_v2',
                                       'filterSettings': {'opacity': 0.0}})
        ret = await ws.call(request)

        # Включаем источник
        # Enabling image source
        request = simpleobsws.Request('SetSceneItemEnabled', {'sceneName': currentSceneName, 'sceneItemId': sourceId,
                                                              'sceneItemEnabled': True})
        ret = await ws.call(request)

        # Получаем размеры источника.
        # Getting source size
        request = simpleobsws.Request('GetSceneItemTransform',
                                      {'sceneName': currentSceneName, 'sceneItemId': sourceId})
        ret = await ws.call(request)

        picWidth = ret.responseData['sceneItemTransform']['width']
        picHeight = ret.responseData['sceneItemTransform']['height']

        # Если картинка больше размеров границ, устанавливаем размеры границ
        # If pic is larger then user's borders, applying custom size for source.
        setNewSize = ret.responseData['sceneItemTransform']
        setNewSize['boundsWidth'] = 1.0
        setNewSize['boundsHeight'] = 1.0
        if picWidth > borderW:
            picWidth = borderW
            setNewSize['width'] = borderW
        if picHeight > borderH:
            picHeight = borderH
            setNewSize['height'] = borderH

        if picHeight >= borderH or picWidth >= borderW:
            setNewSize['positionX'] = borderX
            setNewSize['positionY'] = borderY
            setNewSize['scaleX'] = setNewSize['width']/setNewSize['sourceWidth']
            setNewSize['scaleY'] = setNewSize['height'] / setNewSize['sourceHeight']
        else:
            MaxX = borderX + borderW - picWidth
            MaxY = borderY + borderH - picHeight
            setNewSize['positionX'] = round(random.uniform(borderX, MaxX), 1)
            setNewSize['positionY'] = round(random.uniform(borderY, MaxY), 1)

        # Изменяем размеры источника если они больше установленных пользователем границ в OBS.
        # Resizing source if it's larger then user-defined boundaries in OBS.
        if len(setNewSize) > 0:
            request = simpleobsws.Request('SetSceneItemTransform',
                                          {'sceneName': currentSceneName, 'sceneItemId': sourceId,
                                           'sceneItemTransform': setNewSize})
            ret = await ws.call(request)

            request = simpleobsws.Request('GetSceneItemTransform',
                                          {'sceneName': currentSceneName, 'sceneItemId': sourceId})
            ret = await ws.call(request)

        opacity = 0.01

        # Плавное появление источника с картинкой
        # Smooth appearance of source with pic

        while opacity != 1.0:
            requests.append(simpleobsws.Request('SetSourceFilterSettings',
                                                {'sourceName': sourceName, 'filterName': 'alpha',
                                                 'filterSettings': {'opacity': opacity}}))
            requests.append(simpleobsws.Request('Sleep', {'sleepFrames': 1}))
            opacity = round(opacity + 0.01, 2)

        responses = await ws.call_batch(requests, halt_on_failure=True,
                                        execution_type=simpleobsws.RequestBatchExecutionType.SerialFrame)

        await asyncio.sleep(duracy)

        requests = []
        opacity = 0.99

        # Плавное исчезание источника с картинкой
        # Smooth disappearance of source with pic

        while opacity != 0.0:
            requests.append(simpleobsws.Request('SetSourceFilterSettings',
                                                {'sourceName': sourceName, 'filterName': 'alpha',
                                                 'filterSettings': {'opacity': opacity}}))
            requests.append(simpleobsws.Request('Sleep', {'sleepFrames': 1}))
            opacity = round(opacity - 0.01, 2)

        requests.append(
            simpleobsws.Request('RemoveSceneItem', {'sceneName': currentSceneName, 'sceneItemId': sourceId}))

        responses = await ws.call_batch(requests, halt_on_failure=True,
                                        execution_type=simpleobsws.RequestBatchExecutionType.SerialFrame)

        await ws.disconnect()  # Disconnect from the websocket server cleanly

    def save_config(self, tag, name, value):
        config[tag][name] = value
        with open('settings.ini', 'w', encoding='latin-1') as configfile:  # save ini settings.
            config.write(configfile)

    @commands.command()
    async def wl(self, ctx: commands.Context):
        whitelistAddUser = str(ctx.message.content).replace('!wl ', '').replace('@', '')
        if ctx.author.name == self.InitialChannel:

            # Если это владелец канала
            # If ctx.author is channel author.

            self.save_config('WhiteListUsers', whitelistAddUser, '1')
            await ctx.reply(f'Добавили пользователя @{whitelistAddUser} в вайтлист.')
        elif self.WhiteList_ModsCanAdd is True and ctx.author.is_mod is True:

            # Или если модераторам разрешено добавлять в вайтлист.
            # Or if mods allowed to add users to whitelist directly

            self.save_config('WhiteListUsers', whitelistAddUser, '1')
            await ctx.reply(f'Добавили пользователя @{whitelistAddUser} в вайтлист.')
        else:

            # Если нет, отстраняем пользователя на 10 секунд чтобы не было спама.
            # If not, suspend user for 10 secs to prevent spam.

            await ctx.send(f'/timeout {ctx.author.name} 10 You are not permitted to send this command.')

    @commands.command()
    async def wl_remove(self, ctx: commands.Context):
        whitelistAddUser = str(ctx.message.content).replace('!wl_remove ', '').replace('@', '')
        if ctx.author.name == self.InitialChannel:

            # Если это владелец канала
            # If ctx.author is channel author.

            self.save_config('WhiteListUsers', whitelistAddUser, '0')
            await ctx.reply(f'Удалили пользователя @{whitelistAddUser} из вайтлиста.')
        elif self.WhiteList_ModsCanAdd is True and ctx.author.is_mod is True:

            # Или если модераторам разрешено добавлять в вайтлист.
            # Or if mods allowed to add users to whitelist directly

            self.save_config('WhiteListUsers', whitelistAddUser, '0')
            await ctx.reply(f'Удалили пользователя @{whitelistAddUser} из вайтлиста.')
        else:

            # Если нет, отстраняем пользователя на 10 секунд чтобы не было спама.
            # If not, suspend user for 10 secs to prevent spam.

            await ctx.send(f'/timeout {ctx.author.name} 10 You are not permitted to send this command.')

bot = Bot()
bot.run()