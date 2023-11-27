import datetime
import base64
import io

import requests
from disnake import HTTPException
from disnake.ext import commands
import disnake
from pymongo import MongoClient
import config
from disnake import Option, OptionType


class MyView(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            disnake.SelectOption(
                label="Создать новый канал",
                description="Бот создаст канал и установит чат сам",
                emoji='⚙',
            ),
            disnake.SelectOption(
                label="Выбрать имеющийся",
                description="Вы укажите канал для установки",
                emoji='🗳',
            )
        ]

        super().__init__(
            placeholder="Выберите действие",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select1"
        )

    class MyViewx(disnake.ui.ChannelSelect):
        def __init__(self):
            super().__init__(
                placeholder="Выберите канал",
                channel_types=[disnake.ChannelType.text],
                min_values=1,
                max_values=1,
                custom_id="select2"
            )


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = MongoClient(config.config["database"])
        self.collection = self.cluster.AnonChat.anon
        self.search = self.cluster.AnonChat.search
        self.stats = self.cluster.AnonChat.stats
        self.captcha = self.cluster.AnonChat.captcha
        self.guild = self.cluster.AnonChat.guilds

    @commands.slash_command(name="start", description="Добавляет вас в очередь в анонимный чат", dm_permission=False)
    async def start(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        post2 = {
            "_id": inter.author.id,
            "search": 0,
            "guild": inter.author.guild.id
        }
        if 0 == self.search.count_documents({"_id": inter.author.id}):
            self.search.insert_one(post2)
        find = self.search.find_one({'_id': inter.author.id})['search']
        if find == 1:
            emb = disnake.Embed(title="Вы уже находитесь в режиме поиска", description="Вы можете отключить его в любой момент!",
                                color=disnake.Color.random(), timestamp=datetime.datetime.now())
            emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=emb, ephemeral=True)
        else:
            try:
                comp = self.collection.find_one({'_id': inter.author.id})['comp']
            except:
                comp = 0
            if comp != 0:
                emb = disnake.Embed(title="Вы уже состоите в анонимном чате",
                                    description="Чтобы сменить собеседника нажмите на кнопку \"Стоп\" и начните новый поиск!",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.send(embed=emb, ephemeral=True)
            else:
                self.search.update_one({"_id": inter.author.id}, {"$set": {'search': 1}})
                rows = self.search.find().sort("search", -1)
                succes = False
                for row in rows:
                    if int(inter.author.id) == row["_id"]:
                        continue
                    try:
                        guild = self.search.find_one({'_id': row["_id"]})['guild']
                        guild = await self.bot.fetch_guild(guild)
                    except:
                        guild = None
                    if guild is None:
                        continue
                    else:
                        try:
                            member = await guild.fetch_member(row["_id"])
                        except:
                            member = None
                        if member is None:
                            continue
                        try:
                            last_check = self.collection.find_one({'_id': row["_id"]})['comp']
                        except:
                            last_check = 0
                        if last_check != 0:
                            continue
                        else:
                            try:
                                rep = self.stats.find_one({'_id': row["_id"]})["rep"]
                            except:
                                rep = 0
                            if rep >= 0:
                                emoji = "👍"
                            else:
                                emoji = "👎"
                            emb = disnake.Embed(title="Собеседник найден", description=f"Можете начинать общаться!\nРепутация вашего собеседника: {rep}{emoji}",
                                                color=disnake.Color.random(), timestamp=datetime.datetime.now())

                            if 0 == self.stats.count_documents({"_id": inter.author.id}):
                                rep1 = 0
                            else:
                                try:
                                    rep1 = self.stats.find_one({'_id': inter.author.id})["rep"]
                                except:
                                    rep1 = 0

                            if rep1 >= 0:
                                emoji1 = "👍"
                            else:
                                emoji1 = "👎"
                            emb11 = disnake.Embed(title="Собеседник найден", description=f"Можете начинать общаться!\nРепутация вашего собеседника: {rep1}{emoji1}",
                                                  color=disnake.Color.random(), timestamp=datetime.datetime.now())
                            try:
                                msg = await inter.author.send(embed=emb)
                            except:
                                emb1 = disnake.Embed(title="Закрытая личка", description="У вас закрыта личка! Вы не можете войти в анонимный чат.",
                                                     color=disnake.Color.random(), timestamp=datetime.datetime.now())
                                lol = {"_id": inter.author.id}
                                self.collection.delete_one(lol)
                                self.search.delete_one(lol)
                                await inter.send(embed=emb1, ephemeral=True)
                            else:
                                try:
                                    msg1 = await member.send(embed=emb11)
                                except:
                                    emb2 = disnake.Embed(title="Закрытая личка", description="У вашего собеседника закрытая личка!",
                                                         color=disnake.Color.random(), timestamp=datetime.datetime.now())
                                    lol = {"_id": member.id}
                                    self.collection.delete_one(lol)
                                    self.search.delete_one(lol)
                                    await inter.author.send(embed=emb2)
                                    continue
                                else:
                                    lol = {"_id": member.id}
                                    self.search.delete_one(lol)

                                    lol = {"_id": inter.author.id}
                                    self.search.delete_one(lol)

                                    post1 = {
                                        "_id": inter.author.id,
                                        "guild": inter.guild.id,
                                        "comp": member.id,
                                        "channel": msg.channel.id,
                                        "history": []
                                    }
                                    self.collection.insert_one(post1)

                                    post2 = {
                                        "_id": member.id,
                                        "guild": guild.id,
                                        "comp": inter.author.id,
                                        "channel": msg1.channel.id,
                                        "history": []
                                    }

                                    self.collection.insert_one(post2)

                                    post = {
                                        "_id": inter.author.id,
                                        "messages": 0,
                                        "chats": 0,
                                        "rep": 0,
                                        "warns": 0,
                                        "last_comp": 0,
                                        "bot_chat_id": msg.channel.id,
                                        "banned": 0,
                                        "stop_m": 0,
                                        "aboutme": "Не указано",
                                        "age": 0,
                                        "name": "Не указано",
                                        "gender": 0
                                    }
                                    if 0 == self.stats.count_documents({"_id": inter.author.id}):
                                        self.stats.insert_one(post)
                                    else:
                                        self.stats.update_one({"_id": inter.author.id}, {"$set": {'bot_chat_id': msg.channel.id}})

                                    try:
                                        chats = self.stats.find_one({'_id': inter.author.id})['chats']
                                    except:
                                        chats = 0
                                    self.stats.update_one({"_id": inter.author.id}, {"$set": {'chats': chats + 1}})

                                    self.stats.update_one({"_id": inter.author.id}, {"$set": {'last_comp': member.id}})

                                    post = {
                                        "_id": member.id,
                                        "messages": 0,
                                        "chats": 0,
                                        "rep": 0,
                                        "warns": 0,
                                        "last_comp": 0,
                                        "bot_chat_id": msg1.channel.id,
                                        "banned": 0,
                                        "stop_m": 0,
                                        "aboutme": "Не указано",
                                        "age": 0,
                                        "name": "Не указано",
                                        "gender": "Не указано"
                                    }
                                    if 0 == self.stats.count_documents({"_id": member.id}):
                                        self.stats.insert_one(post)
                                    else:
                                        self.stats.update_one({"_id": member.id}, {"$set": {'bot_chat_id': msg1.channel.id}})

                                    try:
                                        self.stats.update_one({"_id": member.id}, {"$set": {'last_comp': inter.author.id}})
                                    except:
                                        pass

                                    try:
                                        chats1 = self.stats.find_one({'_id': member.id})['chats']
                                    except:
                                        chats1 = 0
                                    self.stats.update_one({"_id": member.id}, {"$set": {'chats': chats1 + 1}})

                                    try:
                                        gg = self.collection.find_one({'_id': member.id})['guild']
                                        chats = self.guild.find_one({'_id': gg})['chats']
                                        self.guild.update_one({"_id": gg}, {"$set": {"chats": chats + 1}})
                                    except:
                                        pass

                                    try:
                                        gg = self.collection.find_one({'_id': inter.author.id})['guild']
                                        chats = self.guild.find_one({'_id': gg})['chats']
                                        self.guild.update_one({"_id": gg}, {"$set": {"chats": chats + 1}})
                                    except:
                                        pass

                                    succes = True

                                    buttons = disnake.ui.View()
                                    buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like", disabled=True))
                                    buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike", disabled=True))
                                    buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report", disabled=True))

                                    try:
                                        channel1 = await self.bot.fetch_channel(self.stats.find_one({'_id': member.id})['bot_chat_id'])
                                    except:
                                        channel1 = None
                                    m1_id = self.stats.find_one({'_id': member.id})['stop_m']
                                    if channel1 is None:
                                        pass
                                    else:
                                        try:
                                            msg1 = await channel1.fetch_message(m1_id)
                                            await msg1.edit(view=buttons)
                                        except:
                                            pass

                                    try:
                                        channel2 = await self.bot.fetch_channel(self.stats.find_one({'_id': inter.author.id})['bot_chat_id'])
                                    except:
                                        channel2 = None
                                    m2_id = self.stats.find_one({'_id': inter.author.id})['stop_m']
                                    if channel2 is None:
                                        pass
                                    else:
                                        try:
                                            msg2 = await channel2.fetch_message(m2_id)
                                            await msg2.edit(view=buttons)
                                        except:
                                            pass

                                    break

                if succes:
                    await inter.delete_original_message()
                else:
                    emb = disnake.Embed(title="Никого нету", description="*К сожалению, собеседника найти не удалось.*\n"
                                                                         "*Но вы можете остаться в режиме поиска и ждать лучших времён!*",
                                        color=disnake.Color.random(), timestamp=datetime.datetime.now())
                    emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    await inter.send(embed=emb, ephemeral=True)

    @commands.slash_command(name="stop", description="Удаляет вас из очереди или чата", dm_permission=True)
    async def stop(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        try:
            findd = self.collection.find_one({'_id': inter.author.id})['comp']
        except:
            findd = 0
        if findd != 0:
            try:
                g2 = self.collection.find_one({'_id': findd})['guild']
                guild_2 = await self.bot.fetch_guild(g2)
            except:
                guild_2 = None

            buttons = disnake.ui.View()
            buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like"))
            buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike"))
            buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report"))

            try:
                member = await guild_2.fetch_member(int(findd))
            except:
                member = None

            try:
                emb = disnake.Embed(title="Конец чата", description="Ваш собеседник остановил чат, увы и ах...",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{member.name}", icon_url=member.avatar)

                m = await member.send(embed=emb, view=buttons)
                self.stats.update_one({"_id": member.id}, {"$set": {'stop_m': m.id}})
            except:
                pass
            try:
                emb1 = disnake.Embed(title="Конец чата", description="Вы остановили чат, класс...\n",
                                     color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb1.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)

                m1 = await inter.author.send(embed=emb1, view=buttons)
                self.stats.update_one({"_id": inter.author.id}, {"$set": {'stop_m': m1.id}})
            except:
                pass

            lol = {"_id": inter.author.id}
            self.collection.delete_one(lol)

            lol = {"_id": findd}
            self.collection.delete_one(lol)

            emb = disnake.Embed(title="Связь разорвана", description="Вы разорвали связть с собеседником и вышли из поиска.",
                                color=disnake.Color.random(), timestamp=datetime.datetime.now())
            emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=emb, ephemeral=True)
        else:
            try:
                x = self.search.count_documents({"_id": inter.author.id})
            except:
                x = 0
            if 0 == x:
                emb = disnake.Embed(title="Ошибка", description="Вы не состоите в поиске собеседника",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.send(embed=emb, ephemeral=True)
            else:
                lol = {"_id": inter.author.id}
                self.search.delete_one(lol)

                emb = disnake.Embed(title="Поиск окончен", description="Вы завершили поиск собеседника",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.send(embed=emb, ephemeral=True)

    @commands.slash_command(name="help", description="Список команд", dm_permission=False)
    async def help(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        embed = disnake.Embed(title="Помощь по боту", description="</start:1130292300795351120> *- войти в анон без установки*\n"
                                                                  "</stop:1130292300795351121> *- выйти из анона без установки*\n\n"
                                                                  "</help:1130292300795351122> *- это сообщение*\n"
                                                                  "</info:1130292300795351123> *- инфа о боте*\n"
                                                                  "</setup:1130292300795351124> *- установить анон*\n"
                                                                  "</unsetup:1130292300795351125> *- удалить анон*\n\n"
                                                                  "</profile:1130297580975292486> *- ваша стата*\n"
                                                                  "</send profile:1167266696017498212> *- отправит профиль*\n"
                                                                  "</bug:1130292300795351129> *- отправить отчёт об ошибке бота*\n\n"
                                                                  "</say:1167220395586375721> *- отправит сообщение от лица бота*\n"
                                                                  "</up:1162465920992673812> *- апнуть бота на [сайте](https://boticord.top/)*",
                              color=disnake.Color.random(), timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=self.bot.user.avatar)
        embed.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
        await inter.send(embed=embed)

    @commands.slash_command(name="info", description="Информация о боте", dm_permission=False)
    async def info(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        ping = self.bot.latency * 1000

        emb = disnake.Embed(title=f"Информация о боте",
                            description=f"・ *Developer -*  **xlvlocl**\n"
                                        f"・ **[Сервер поддержки](https://discord.gg/4cuBcTrjh4)**\n"
                                        f"・ *Оставить отзыв* **[тут](https://bots.server-discord.com/1078924878071214110)** *и* **[тут](https://boticord.top/bot/1078924878071214110)**\n\n"
                                        f"・ *Пинг -*  **{int(ping)}** *мс*\n"
                                        f"・ *Серверов -*  **{len(self.bot.guilds)}**\n"
                                        f"・ **[Добавить бота](https://discord.com/api/oauth2/authorize?client_id=1078924878071214110&permissions=67632&scope=bot%20applications.commands)**",
                            colour=disnake.Color.random(), timestamp=datetime.datetime.now())

        emb.set_thumbnail(url=self.bot.user.avatar)
        emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
        await inter.send(embed=emb)

    @commands.slash_command(name="setup", description="Установить анон-чат", dm_permission=False)
    @commands.default_member_permissions(administrator=True)
    async def setup(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        post = {
            '_id': inter.guild.id,
            'channel': 0,
            'chats': 0,
            'messages': 0
        }
        if 0 == self.guild.count_documents({"_id": inter.guild.id}):
            self.guild.insert_one(post)

        try:
            channel = self.guild.find_one({'_id': inter.guild.id})['channel']
        except:
            channel = 0

        if channel != 0:
            embx = disnake.Embed(title="Ошибка", description=f"На этом сервере уже установлен анонимный чат!\n"
                                                             f"Если вы хотите его удалить, то используйте команду </unsetup:1130292300795351125>",
                                 color=disnake.Color.random(), timestamp=datetime.datetime.now())
            embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=embx)
        else:
            view = disnake.ui.View()
            view.add_item(MyView())
            await inter.send(view=view)

    @commands.Cog.listener()
    async def on_interaction(self, inter: disnake.MessageInteraction):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        try:
            a = inter.component.custom_id
        except:
            a = None
        if a == "select1":
            if inter.values[0] == "Создать новый канал":
                if inter.guild.id == 680172831132352520:
                    buttons = disnake.ui.View()
                    buttons.add_item(disnake.ui.Button(label='Старт', emoji='<:1_:1064240182422945842> ', style=disnake.ButtonStyle.gray, custom_id="start"))
                    buttons.add_item(disnake.ui.Button(label='Стоп', emoji='<:__:1064242340954390538> ', style=disnake.ButtonStyle.gray, custom_id="stop"))
                    buttons.add_item(disnake.ui.Button(label='Справка', emoji='<:1_:1064243510938718218> ', style=disnake.ButtonStyle.gray, custom_id="info"))
                    emb = disnake.Embed(color=0xffff00)
                    emb1 = disnake.Embed(title="Совет", description=f"Рекомендую отключить участникам возможность писать в этот канал!\n"
                                                                    f"Это сообщение будет автоматически удалено через 30 секунд", color=disnake.Color.random(), timestamp=datetime.datetime.now())
                    emb.set_image("https://cdn.discordapp.com/attachments/971521760732258397/1145105423268073532/standard_1.gif")
                else:
                    buttons = disnake.ui.View()
                    buttons.add_item(disnake.ui.Button(label='Старт', emoji='<:321:1095340832711770222>', style=disnake.ButtonStyle.gray, custom_id="start"))
                    buttons.add_item(disnake.ui.Button(label='Стоп', emoji='<:123:1095340836826394644>', style=disnake.ButtonStyle.gray, custom_id="stop"))
                    buttons.add_item(disnake.ui.Button(label='Инфо', emoji='<:456:1095340827896725504>', style=disnake.ButtonStyle.gray, custom_id="info"))
                    emb1 = disnake.Embed(title="Совет", description=f"Рекомендую отключить участникам возможность писать в этот канал!\n"
                                                                    f"Это сообщение будет автоматически удалено через 30 секунд", color=disnake.Color.random(), timestamp=datetime.datetime.now())
                    emb = disnake.Embed(color=disnake.Color.dark_gray())
                    emb.set_image(file=disnake.File('files/banner.png'))
                try:
                    channel = await inter.channel.category.create_text_channel("Анонимный чат")
                    await channel.send(embed=emb, view=buttons)
                    await channel.send(embed=emb1, delete_after=30)
                    self.guild.update_one({"_id": inter.guild.id}, {"$set": {'channel': int(channel.id)}})
                except:
                    try:
                        channel = await inter.guild.create_text_channel("Анонимный чат")
                        await channel.send(embed=emb, view=buttons)
                        await channel.send(embed=emb1, delete_after=30)
                        self.guild.update_one({"_id": inter.guild.id}, {"$set": {'channel': int(channel.id)}})
                        await inter.delete_original_message()
                    except:
                        embx = disnake.Embed(title="Ошибка", description=f"У бота нет права писать в этот канал / создавать канал",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                        await inter.delete_original_message()
                        await inter.send(embed=embx, ephemeral=True)
                    else:
                        embx = disnake.Embed(title="Успешно!", description=f"*Анонимный чат установлен в канале* {channel.mention}",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                        await inter.send(embed=embx, ephemeral=True)
                else:
                    embx = disnake.Embed(title="Успешно!", description=f"*Анонимный чат установлен в канале* {channel.mention}",
                                         color=disnake.Color.random(), timestamp=datetime.datetime.now())
                    embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    await inter.delete_original_message()
                    await inter.send(embed=embx, ephemeral=True)
            else:
                view = disnake.ui.View()
                view.add_item(MyView.MyViewx())
                await inter.edit_original_response(view=view)
        elif a == "select2":
            if inter.guild.id == 680172831132352520:
                buttons = disnake.ui.View()
                buttons.add_item(disnake.ui.Button(label='Старт', emoji='<:1_:1064240182422945842> ', style=disnake.ButtonStyle.gray, custom_id="start"))
                buttons.add_item(disnake.ui.Button(label='Стоп', emoji='<:__:1064242340954390538> ', style=disnake.ButtonStyle.gray, custom_id="stop"))
                buttons.add_item(disnake.ui.Button(label='Справка', emoji='<:1_:1064243510938718218> ', style=disnake.ButtonStyle.gray, custom_id="info"))
                emb = disnake.Embed(color=0xffff00)
                emb1 = disnake.Embed(title="Совет", description=f"Рекомендую отключить участникам возможность писать в этот канал!\n"
                                                                f"Это сообщение будет автоматически удалено через 30 секунд", color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_image("https://cdn.discordapp.com/attachments/971521760732258397/1145105423268073532/standard_1.gif")
            else:
                buttons = disnake.ui.View()
                buttons.add_item(disnake.ui.Button(label='Старт', emoji='<:321:1095340832711770222>', style=disnake.ButtonStyle.gray, custom_id="start"))
                buttons.add_item(disnake.ui.Button(label='Стоп', emoji='<:123:1095340836826394644>', style=disnake.ButtonStyle.gray, custom_id="stop"))
                buttons.add_item(disnake.ui.Button(label='Инфо', emoji='<:456:1095340827896725504>', style=disnake.ButtonStyle.gray, custom_id="info"))

                emb = disnake.Embed(color=disnake.Color.dark_gray())
                emb.set_image(file=disnake.File('files/banner.png'))
            channel = inter.guild.get_channel(int(inter.values[0]))
            try:
                msg = await channel.send(embed=emb, view=buttons)
            except:
                emb = disnake.Embed(title="Ошибка", description=f"У бота нет права писать в этот канал.",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.send(embed=emb, ephemeral=True)
            else:
                await channel.send(embed=disnake.Embed(title="Совет", description=f"Рекомендую отключить участникам возможность писать в этот канал!\n"
                                                                                  f"Это сообщение будет автоматически удалено через 30 секунд", color=disnake.Color.random(), timestamp=datetime.datetime.now()), delete_after=30)

                self.guild.update_one({"_id": inter.guild.id}, {"$set": {'channel': int(channel.id)}})

                embx = disnake.Embed(title="Успешно!", description=f"*Анонимный чат установлен в канале* {channel.mention}",
                                     color=disnake.Color.random(), timestamp=datetime.datetime.now())
                embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.delete_original_message()
                await inter.send(embed=embx, ephemeral=True)

    @commands.slash_command(name="unsetup", description="Отключить анон-чат", dm_permission=False)
    @commands.default_member_permissions(administrator=True)
    async def unsetup(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        try:
            channel = self.guild.find_one({'_id': inter.guild.id})['channel']
        except:
            embx = disnake.Embed(title="Ошибка!", description=f"Анонимный чат не был включен!",
                                 color=disnake.Color.random(), timestamp=datetime.datetime.now())
            embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=embx)
        else:
            class buttons(disnake.ui.View):
                def __init__(self, bot=self.bot):
                    super().__init__(timeout=30)
                    self.bot = bot
                    self.cluster = MongoClient(config.config["database"])
                    self.guild = self.cluster.AnonChat.guilds

                async def on_timeout(self):
                    try:
                        await inter.delete_original_message()
                    except:
                        pass

                @disnake.ui.button(label='Подтвердить', emoji='✅', style=disnake.ButtonStyle.gray)
                async def conf(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
                    try:
                        await inter.response.defer(ephemeral=True)
                    except HTTPException:
                        pass
                    self.guild.update_one({"_id": inter.guild.id}, {"$set": {"channel": 0}})
                    try:
                        ch = inter.guild.get_channel(int(channel))
                        await ch.delete()
                    except:
                        embx = disnake.Embed(title="Ошибка", description=f"Анонимный чат отключен, но бот не смог удалить канал!",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                        try:
                            await inter.delete_original_message()
                            await inter.send(embed=embx, ephemeral=True)
                        except:
                            pass
                    else:
                        embx = disnake.Embed(title="Успешно!", description=f"Анонимный чат отключен!",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                        try:
                            await inter.delete_original_message()
                            await inter.send(embed=embx, ephemeral=True)
                        except:
                            pass

                @disnake.ui.button(label='Отменить', emoji='❌', style=disnake.ButtonStyle.gray)
                async def canc(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
                    try:
                        await inter.response.defer(ephemeral=True)
                    except HTTPException:
                        pass
                    try:
                        await inter.delete_original_message()
                    except:
                        pass

                @disnake.ui.button(label='Отключить без удаления', emoji='⚠', style=disnake.ButtonStyle.gray)
                async def dell(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
                    try:
                        await inter.response.defer(ephemeral=True)
                    except HTTPException:
                        pass
                    self.guild.update_one({"_id": inter.guild.id}, {"$set": {"channel": 0}})
                    ch = inter.guild.get_channel(int(channel))
                    if ch is not None:
                        try:
                            await ch.purge(limit=None, check=lambda m: m.author == self.bot.user)
                        except:
                            pass
                        embx = disnake.Embed(title="Успешно!", description=f"Анонимный чат отключен!",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    else:
                        embx = disnake.Embed(title="Успешно!", description=f"Анонимный чат отключен!",
                                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        embx.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    try:
                        await inter.delete_original_message()
                        await inter.send(embed=embx, ephemeral=True)
                    except:
                        pass

            try:
                ch = inter.guild.get_channel(int(channel))
            except:
                ch = None
            if ch is not None:
                embed = disnake.Embed(title="Подтвердите ваши намерения", description=f"*После подтверждения действия бот* **удалит** *канал* **{ch.mention},** *вы уверены?*", color=disnake.Color.red(), timestamp=datetime.datetime.now())
                embed.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            else:
                embed = disnake.Embed(title="Подтвердите ваши намерения", description=f"*После подтверждения действия бот* **удалит** *канал с анонимным чатом* *вы уверены?*", color=disnake.Color.red(), timestamp=datetime.datetime.now())
                embed.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            message = await inter.send(embed=embed, view=buttons())

    @commands.slash_command(
        name='send',
        description="",
        dm_permission=True)
    async def sendpr(self, inter):
        pass

    @sendpr.sub_command(
        name='profile',
        description=f'Отправит вашему собеседнику ваш профиль')
    async def sendprofile(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        post = {
            "_id": inter.author.id,
            "messages": 0,
            "chats": 0,
            "rep": 0,
            "warns": 0,
            "last_comp": 0,
            "bot_chat_id": 0,
            "banned": 0,
            "stop_m": 0,
            "aboutme": "Не указано",
            "age": 0,
            "name": "Не указано",
            "gender": "Не указано"
        }
        if 0 == self.stats.count_documents({"_id": inter.author.id}):
            self.stats.insert_one(post)
        try:
            comp = self.collection.find_one({'_id': inter.author.id})['comp']
        except:
            comp = 0
        if comp is None or comp == 0:
            emb = disnake.Embed(title="Ошибка!",
                                description="Вы не состоите в анонимном чате!",
                                color=disnake.Color.red(), timestamp=datetime.datetime.now())
            emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=emb, ephemeral=True)
        else:
            try:
                guild = self.collection.find_one({'_id': comp})['guild']
                guild = await self.bot.fetch_guild(guild)
            except:
                guild = None
            if guild is None:
                pass
            else:
                try:
                    rep = self.stats.find_one({'_id': inter.author.id})['rep']
                except:
                    rep = 0
                if rep >= 0:
                    emoji = "👍"
                else:
                    emoji = "👎"

                name = self.stats.find_one({'_id': inter.author.id})['name']
                age = self.stats.find_one({'_id': inter.author.id})['age']
                gender = self.stats.find_one({'_id': inter.author.id})['gender']
                aboutme = self.stats.find_one({'_id': inter.author.id})['aboutme']

                emb = disnake.Embed(title=f"Ваш собеседник отправил свой профиль", description=f"Имя **{name}**\n"
                                                                                               f"Возраст **{'Не указан' if age == 0 else age}**\n"
                                                                                               f"Пол **{gender}**\n\n"
                                                                                               f"Обо мне\n`{aboutme}`\n\n"
                                                                                               f"*Его ник:* **[{inter.author.name}](https://discordapp.com/users/{inter.author.id}/)**\n"
                                                                                               f"*Пинг:* {inter.author.mention}",
                                    color=disnake.Color.random(), timestamp=datetime.datetime.now())
                emb.set_thumbnail(url=inter.author.avatar)
                emb.set_footer(text=f"{inter.author.name} | {inter.author.id}", icon_url=inter.author.avatar)
                try:
                    memberx = await guild.fetch_member(comp)
                    await memberx.send(embed=emb)
                except:
                    emb = disnake.Embed(title="Ошибка!",
                                        description="Я не смог отправить собеседнику ваш профиль!",
                                        color=disnake.Color.red(), timestamp=datetime.datetime.now())
                    emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    await inter.send(embed=emb, ephemeral=True)
                else:
                    emb = disnake.Embed(title="Успешно",
                                        description="Вы отправили собеседнику свой профиль!",
                                        color=disnake.Color.random(), timestamp=datetime.datetime.now())
                    emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                    await inter.send(embed=emb, ephemeral=True)

    @commands.slash_command(name="profile", description="Показывает профиль указанного пользователя (вас если не указан)", dm_permission=False,
                            options=[
                                Option("member", "Укажите пользователя", OptionType.user, required=False),
                            ])
    async def profile(self, inter, member=None):
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        if member is None:
            member = inter.author
        post = {
            "_id": member.id,
            "messages": 0,
            "chats": 0,
            "rep": 0,
            "warns": 0,
            "last_comp": 0,
            "bot_chat_id": 0,
            "banned": 0,
            "stop_m": 0,
            "aboutme": "Не указано",
            "age": 0,
            "name": "Не указано",
            "gender": "Не указано"
        }
        if 0 == self.stats.count_documents({"_id": member.id}):
            self.stats.insert_one(post)

        messages = self.stats.find_one({'_id': member.id})['messages']
        chats = self.stats.find_one({'_id': member.id})['chats']
        try:
            rep = self.stats.find_one({'_id': member.id})['rep']
        except:
            rep = 0
        if rep >= 0:
            emoji = "👍"
        else:
            emoji = "👎"

        class Buttons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            async def on_timeout(self):
                try:
                    await inter.delete_original_message()
                except:
                    pass

            @disnake.ui.button(emoji="⚙", label="Настроить", style=disnake.ButtonStyle.grey)
            async def previous(self, button, inter):
                await inter.response.send_modal(MyModal())

        class MyModal(disnake.ui.Modal):
            def __init__(self):
                # Детали модального окна и его компонентов
                self.cluster = MongoClient(config.config["database"])
                self.stats = self.cluster.AnonChat.stats
                components = [
                    disnake.ui.TextInput(
                        label="Имя",
                        placeholder="Олег",
                        custom_id="name",
                        style=disnake.TextInputStyle.short,
                        max_length=16,
                        min_length=2
                    ),
                    disnake.ui.TextInput(
                        label="Возраст",
                        placeholder="14+",
                        custom_id="age",
                        style=disnake.TextInputStyle.single_line,
                        max_length=2,
                        min_length=2
                    ),
                    disnake.ui.TextInput(
                        label="Пол",
                        placeholder="М/Ж",
                        custom_id="gender",
                        style=disnake.TextInputStyle.single_line,
                        max_length=1,
                        min_length=1
                    ),
                    disnake.ui.TextInput(
                        label="Обо мне",
                        placeholder="Саня, разраб бота, молодец в общем",
                        custom_id="aboutme",
                        style=disnake.TextInputStyle.single_line,
                        max_length=75,
                        min_length=10
                    )
                ]
                super().__init__(
                    title="Профиль",
                    custom_id="profile",
                    components=components,
                )

            async def callback(self, interr: disnake.ModalInteraction):
                for key, value in interr.text_values.items():
                    if key.capitalize() == "Name":
                        self.stats.update_one({"_id": member.id}, {"$set": {'name': value}})
                    if key.capitalize() == "Age":
                        try:
                            value = int(value)
                        except:
                            pass
                        else:
                            self.stats.update_one({"_id": member.id}, {"$set": {'age': value}})
                    if key.capitalize() == "Gender":
                        if value.lower() == "м":
                            self.stats.update_one({"_id": member.id}, {"$set": {'gender': "Мужской"}})
                        elif value.lower() == "ж":
                            self.stats.update_one({"_id": member.id}, {"$set": {'gender': "Женский"}})
                    if key.capitalize() == "Aboutme":
                        self.stats.update_one({"_id": member.id}, {"$set": {'aboutme': value}})

                emb = disnake.Embed(title="Успешно!", description="Вы обновили свой профиль",
                                    color=disnake.Color.random())
                emb.set_footer(text=f"{interr.author}", icon_url=inter.author.avatar)
                await interr.send(embed=emb, ephemeral=True)

        name = self.stats.find_one({'_id': member.id})['name']
        age = self.stats.find_one({'_id': member.id})['age']
        gender = self.stats.find_one({'_id': member.id})['gender']
        aboutme = self.stats.find_one({'_id': member.id})['aboutme']

        emb1 = disnake.Embed(title=f"Профиль {member.name}", description="",
                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
        emb1.set_thumbnail(url=member.avatar)
        emb1.set_footer(text=f"{member.name} | {member.id}", icon_url=member.avatar)
        emb1.add_field(name="Имя:", value=f"`{name}`", inline=True)
        emb1.add_field(name="Возраст:", value=f"`{'Не указан' if age == 0 else age}`", inline=True)
        emb1.add_field(name="Пол:", value=f"`{gender}`", inline=True)
        emb1.add_field(name="Обо мне:", value=f"`{aboutme}`", inline=False)
        emb1.add_field(name="Был в чатах:", value=f"`{chats}`", inline=True)
        emb1.add_field(name="Написал сообщений:", value=f"`{messages}`", inline=True)
        emb1.add_field(name="Репутация:", value=f"`{rep}`{emoji}", inline=True)

        if member == inter.author:
            await inter.send(embed=emb1, view=Buttons())
        else:
            await inter.send(embed=emb1)

    @commands.slash_command(name="bug", description="Отправить отчёт об ошибке в боте", dm_permission=False)
    async def bug(self, inter, text: str = commands.Param(name="проблема", description="пишите, в чём заключается баг и как он получается", min_length=50), att: disnake.Attachment = commands.Param(name="скриншот", description="Покажите реакцию от бота при баге")):
        """Отправляет администрации вашу жалобу"""
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            pass
        emb1 = disnake.Embed(title=f"Баг отправлен!",
                             description=f'{inter.author.mention}, в скором времени разработчик устранит эту ошибку, спасибо за помощь!',
                             color=disnake.Color.random(), timestamp=datetime.datetime.now())
        await inter.send(embed=emb1)
        emb = disnake.Embed(title=f"Нашли новый баг!",
                            description=f"**Отправитель:** {inter.author}\n**ID:** {inter.author.id}\n**Подробности:**\n\n`{text}`",
                            color=disnake.Color.random(), timestamp=datetime.datetime.now())

        emb.set_thumbnail(url=inter.author.avatar)
        emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
        emb.set_image(url=att)
        guild = await self.bot.fetch_guild(1103758994398523432)
        channel = await guild.fetch_channel(1103761364910100590)
        await channel.send(content=f"{inter.author.mention}", embed=emb)

    @commands.slash_command(name="up", description="Апнуть бота", dm_permission=False)
    async def up(self, inter: disnake.CommandInteraction):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        response = requests.post(
            url='https://api.boticord.top/v3/resources/ups/service/prepare',
            headers={
                'Authorization': config.config['Boticord'],
                'Content-Type': 'application/json'
            },
            json={
                "token": config.config['Boticord'],
                "resource": "1078924878071214110",
                "user": str(inter.author.id),
                "language": "ru"
            }
        )

        if response.status_code == 201:
            data = response.json()
            img_data = data['result']['captcha']['image'].encode()
            content = base64.b64decode(img_data)
            bytes = io.BytesIO(content)

            user = self.captcha.find_one({'_id': inter.author.id})
            if user is None:
                post = {
                    "_id": inter.author.id,
                    "captcha": data['result']['captcha']['id']
                }
                self.captcha.insert_one(post)
            else:
                self.captcha.update_one({"_id": inter.author.id}, {"$set": {'captcha': data['result']['captcha']['id']}})

            buttons = disnake.ui.View()

            buttons.add_item(disnake.ui.Button(
                label='',
                emoji=f'{data["result"]["captcha"]["choices"][0]}',
                style=disnake.ButtonStyle.gray,
                custom_id="btn1")
            )
            buttons.add_item(disnake.ui.Button(
                label='',
                emoji=f'{data["result"]["captcha"]["choices"][1]}',
                style=disnake.ButtonStyle.gray,
                custom_id="btn2")
            )
            buttons.add_item(disnake.ui.Button(
                label='',
                emoji=f'{data["result"]["captcha"]["choices"][2]}',
                style=disnake.ButtonStyle.gray,
                custom_id="btn3")
            )

            emb = disnake.Embed(
                title="Решите капчу",
                description="Выбери эмоцию, соответствующую тексту на картинке",
                color=disnake.Color.random(),
                timestamp=datetime.datetime.now()
            )
            emb.set_image(file=disnake.File(bytes, filename="captcha.png"))
            emb.set_thumbnail(inter.author.avatar)
            emb.set_footer(text=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")
            await inter.edit_original_message(embed=emb, view=buttons)
        elif response.status_code == 429:
            emb = disnake.Embed(
                title="Ошибка",
                description="Вы уже недавно апали этого бота!",
                color=disnake.Color.random(),
                timestamp=datetime.datetime.now()
            )
            emb.set_thumbnail(inter.author.avatar)
            emb.set_footer(text=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")
            await inter.delete_original_message()
            await inter.send(embed=emb, ephemeral=True)
        else:
            emb = disnake.Embed(
                title="Ошибка",
                description="Скорее всего вы ни разу не авторизовывались на сайте [Boticord](https://boticord.top/)\n"
                            "Если же это не так, попробуйте повторить попытку позже.",
                color=disnake.Color.random(),
                timestamp=datetime.datetime.now()
            )
            emb.set_thumbnail(inter.author.avatar)
            emb.set_footer(text=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")
            await inter.delete_original_message()
            await inter.send(embed=emb, ephemeral=True)


def setup(bot):
    bot.add_cog(Slash(bot))
