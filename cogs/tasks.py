import asyncio
import datetime
import os
import signal

import requests
import disnake
from disnake.ext import commands, tasks
from pymongo import MongoClient
import config

import Logger

logger = Logger.Logger()


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status.start()
        self.sdc_timer.start()
        self.boticord_timer.start()

        self.cluster = MongoClient(config.config["database"])
        self.collection = self.cluster.AnonChat.anon
        self.search = self.cluster.AnonChat.search
        self.coll = self.cluster.AnonChat.guilds

    def cog_unload(self):
        self.status.close()
        self.sdc_timer.close()
        self.boticord_timer.close()
        return

    @tasks.loop(seconds=3600)
    async def sdc_timer(self):
        await self.bot.wait_until_ready()
        response = requests.post(url='https://api.server-discord.com/v2/bots/1078924878071214110/stats', headers={"Authorization": config.config["SDC"]},
                                 json={'servers': len(self.bot.guilds), 'shards': 1})
        if response.status_code == 200:
            pass
        else:
            print(response.status_code, " SDC")

    @tasks.loop(seconds=900)
    async def boticord_timer(self):
        await self.bot.wait_until_ready()
        stats = {'servers': len(self.bot.guilds)}
        response = requests.post(url='https://api.boticord.top/v3/bots/1078924878071214110/stats', headers={
            "Authorization": config.config['Boticord'],
            'Content-Type': 'application/json'
        },
                                 json=stats)
        if response.status_code == 201:
            pass
        else:
            print(response.content, " Boticord")

    @tasks.loop(seconds=30)
    async def status(self):
        await self.bot.wait_until_ready()
        await self.bot.change_presence(
            status=disnake.Status.online,
            activity=disnake.Activity(name=f"/help", type=disnake.ActivityType.playing),
        )
        await asyncio.sleep(15)
        await self.bot.change_presence(
            status=disnake.Status.online,
            activity=disnake.Activity(
                name=f"за {len(self.bot.guilds)} серверами", type=disnake.ActivityType.watching
            ),
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        lol1 = {"_id": member.id}
        self.search.delete_one(lol1)
        try:
            guild = self.collection.find_one({"_id": member.id})["guild"]
        except:
            guild = None
        if guild == member.guild.id:
            try:
                compID = self.collection.find_one({"_id": member.id})["comp"]
            except:
                compID = None
            try:
                compGuild = self.collection.find_one({"_id": compID})["guild"]
            except:
                compGuild = None
            if compGuild is not None:
                g = await self.bot.fetch_guild(compGuild)
            else:
                g = None
            buttons = disnake.ui.View()
            buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like"))
            buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike"))
            buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report"))

            try:
                memberx = await self.bot.fetch_member(compID)
                await memberx.send(
                    embed=disnake.Embed(
                        title="Конец чата",
                        description="Ваш собеседник остановил чат, увы и ах...\n",
                        color=disnake.Color.random(), timestamp=datetime.datetime.now()
                    ), view=buttons
                )
            except:
                pass
            try:
                emb1 = disnake.Embed(
                    title="Конец чата",
                    description="Вы остановили чат, класс...",
                    color=disnake.Color.random(), timestamp=datetime.datetime.now()
                )
                await member.send(embed=emb1, view=buttons)

            except:
                pass
            lol1 = {"_id": member.id}
            self.collection.delete_one(lol1)

            lol = {"_id": compID}
            self.collection.delete_one(lol)
        else:
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        lol = {"_id": guild.id}
        self.coll.delete_one(lol)

        peoplex = self.collection.find()
        for people in peoplex:
            if people["guild"] == guild.id:
                compID = people["comp"]

                a = {"_id": people["_id"]}
                self.collection.delete_one(a)
                self.search.delete_one(a)

                if compID == 0:
                    pass
                else:
                    try:
                        compGuild = self.collection.find_one({'_id': compID})['guild']
                    except:
                        compGuild = None
                    try:
                        g = await self.bot.fetch_guild(compGuild)
                    except:
                        g = None
                    if g is None:
                        continue
                    else:
                        memberx = await self.bot.fetch_user(compID)

                        a = {"_id": memberx.id}
                        self.collection.delete_one(a)
                        self.search.delete_one(a)

                        try:
                            await memberx.send(
                                embed=disnake.Embed(
                                    title="Конец чата",
                                    description="Бота удалили с сервера вашего собеседника. Я вынужен отключить вас.\n",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now()
                                )
                            )
                        except:
                            pass
                        try:
                            member = await self.bot.fetch_user(people["_id"])
                        except:
                            member = None
                        try:
                            emb1 = disnake.Embed(
                                title="Конец чата",
                                description="С сервера, на котором вы зашли в анонимный чат удалили бота.\n",
                                color=disnake.Color.random(), timestamp=datetime.datetime.now()
                            )
                            await member.send(embed=emb1)
                        except:
                            pass
            else:
                continue

        peopl = self.search.find()
        for n in peopl:
            a = {"_id": n["_id"]}
            self.search.delete_one(a)

        guilds = await self.bot.fetch_guild(1103758994398523432)
        channel = await guilds.fetch_channel(1103762413372837918)
        emb = disnake.Embed(
            title=f"Убрали сервер",
            description=f"❌ Бота удалили с сервера **{guild.name}** ({guild.member_count} участников)",
            color=disnake.Color.red(), timestamp=datetime.datetime.now()
        )
        emb.set_thumbnail(guild.icon)
        emb.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon)
        await channel.send(embed=emb)


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        post = {
            '_id': guild.id,
            'channel': 0,
            'chats': 0,
            'messages': 0
        }
        if 0 == self.coll.count_documents({"_id": guild.id}):
            self.coll.insert_one(post)

        channels = guild.text_channels
        invite = None
        for i in channels:
            try:
                invite = await i.create_invite(unique=True, temporary=False)
            except:
                continue
            if invite is not None:
                break
            else:
                continue

        async def get_user_who_invited_bot(guild):
            integrations = await guild.integrations()

            bot_integration = next(
                (
                    integration
                    for integration in integrations
                    if isinstance(integration, disnake.BotIntegration) and integration.application.user.name == self.bot.user.name
                ),
                None,
            )

            return bot_integration.user if bot_integration else None

        try:
            user = await get_user_who_invited_bot(guild)
            emb1 = disnake.Embed(title="👋 ┃ Спасибо, что добавили бота!", description=f"*Привет* {user.mention}, *ты добавил* **AnonChat** *на сервер* **{guild.name}**, *поэтому получил это сообщение. Ознакомься с текстом ниже, чтобы понимать как пользоваться и настраивать бота!*",
                                 color=disnake.Color.random())
        except:
            user = None
            emb1 = None

        emb = disnake.Embed(title="⚙️ ┃ Начальная настройка", description=f"> *Привет, я* **AnonChat** *- бот для анонимного общения в лс.*\n"
                                                                          f"> *Чтобы пользоваться мною используйте слэш команды* </start:1130292300795351120> *и* </stop:1130292300795351121>\n\n"
                                                                          f"> *Также для удобного пользования ботом вы можете назначить специальный канал для анонимного чата командой </setup:1130292300795351124>*\n\n"
                                                                          f"> *Вы можете отправить отчёт об ошибке в боте командой* </bug:1130292300795351129> *или зайдти на* **[саппорт сервер](https://discord.gg/4cuBcTrjh4)**\n\n"
                                                                          f"> *Команды для более подробной информации:* </help:1130292300795351122> | </info:1130292300795351123>\n"
                                                                          f"### Важно: бот ищет собеседников СО ВСЕХ серверов, на которых установлен. Поэтому не стоит переживать, если у вас маленький сервер :)\n"
                                                                          f"> *Оставить отзыв боту можно на* **[bots.server](https://bots.server-discord.com/1078924878071214110)** *или на* **[boticord](https://boticord.top/bot/1078924878071214110)**\n"
                                                                          f"> *Апнуть бота на [сайте](https://boticord.top/) можно с помощью команды* </up:1162465920992673812>", color=disnake.Color.random(), timestamp=datetime.datetime.now())
        emb.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon)
        emb.set_image(file=disnake.File('files/banner.png'))

        try:
            await user.send(embeds=[emb1, emb])
        except:
            for channel in channels:
                try:
                    await channel.send(embed=emb)
                    break
                except:
                    continue

        guilds = await self.bot.fetch_guild(1103758994398523432)
        channel = await guilds.fetch_channel(1103762413372837918)
        emb = disnake.Embed(title=f"Новый сервер", description=f"✅ Бот зашёл на сервер **{guild.name}** ({guild.member_count} участников)\n[Ссылка]({invite})", color=disnake.Color.green(), timestamp=datetime.datetime.now())
        emb.set_thumbnail(guild.icon)
        emb.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon)
        await channel.send(embed=emb)


def setup(bot):
    bot.add_cog(Tasks(bot))
