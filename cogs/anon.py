import datetime
import disnake
import requests
from disnake.ext import commands
from pymongo import MongoClient
import config


class Anon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = MongoClient(config.config["database"])
        self.collection = self.cluster.AnonChat.anon
        self.search = self.cluster.AnonChat.search
        self.coll = self.cluster.AnonChat.guilds
        self.stats = self.cluster.AnonChat.stats
        self.reports = self.cluster.AnonChat.reports
        self.captcha = self.cluster.AnonChat.captcha
        self.guild = self.cluster.AnonChat.guilds

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "start":
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
                        pass
                    else:
                        emb = disnake.Embed(title="Никого нету", description="*К сожалению, собеседника найти не удалось.*\n"
                                                                             "*Но вы можете остаться в режиме поиска и ждать лучших времён!*",
                                            color=disnake.Color.random(), timestamp=datetime.datetime.now())
                        emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                        await inter.send(embed=emb, ephemeral=True)

        elif inter.component.custom_id == "stop":
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

        elif inter.component.custom_id == "info":
            try:
                await inter.response.defer()
            except:
                pass
            emb = disnake.Embed(title="Справка по анонимному чату", description="**Старт** *- начать поиск*\n"
                                                                                "**Стоп** *- закончить поиск/чат*\n"
                                                                                "**Глобальное правило:** *Не отправлять ссылки на сервера. Карается ПЕРМАНЕНТНЫМ ограничением доступа к анон чату*\n\n"
                                                                                "Если есть вопросы/предложения заходи на [саппорт сервер](https://discord.gg/7hmGhQbMUQ)\n\n"
                                                                                "> 😈 Партнёрские сервера: [Suck Or Play](https://discord.gg/yj34kKnFvU) & [Neró](https://discord.gg/X46WYJTBAy)",
                                color=disnake.Color.random(), timestamp=datetime.datetime.now())
            emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
            await inter.send(embed=emb, ephemeral=True)

        elif inter.component.custom_id == "like":
            try:
                await inter.response.defer()
            except:
                pass
            try:
                last_comp = self.stats.find_one({'_id': inter.author.id})['last_comp']
            except:
                pass
            else:
                buttons = disnake.ui.View()
                buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like", disabled=True))
                buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike", disabled=True))
                buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report"))
                try:
                    likes = self.stats.find_one({'_id': last_comp})['rep']
                    self.stats.update_one({"_id": last_comp}, {"$set": {'rep': likes + 1}})
                except:
                    pass
                emb = disnake.Embed(title="Лайк!", description="Вы поставили собеседнику лайк.",
                                    color=disnake.Color.green(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.edit_original_response(view=buttons)
                await inter.send(embed=emb)

        elif inter.component.custom_id == "dlike":
            try:
                await inter.response.defer()
            except:
                pass
            try:
                last_comp = self.stats.find_one({'_id': inter.author.id})['last_comp']
            except:
                pass
            else:
                buttons = disnake.ui.View()
                buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like", disabled=True))
                buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike", disabled=True))
                buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report"))
                try:
                    likes = self.stats.find_one({'_id': last_comp})['rep']
                    self.stats.update_one({"_id": last_comp}, {"$set": {'rep': likes - 1}})
                except:
                    pass
                emb = disnake.Embed(title="Дизлайк", description="Вы поставили собеседнику дизлайк.",
                                    color=disnake.Color.red(), timestamp=datetime.datetime.now())
                emb.set_footer(text=f"{inter.author.name}", icon_url=inter.author.avatar)
                await inter.edit_original_response(view=buttons)
                await inter.send(embed=emb)
        elif inter.component.custom_id == "report":
            buttons = disnake.ui.View()
            buttons.add_item(disnake.ui.Button(label='', emoji='👍', style=disnake.ButtonStyle.gray, custom_id="like", disabled=True))
            buttons.add_item(disnake.ui.Button(label='', emoji='👎', style=disnake.ButtonStyle.gray, custom_id="dlike", disabled=True))
            buttons.add_item(disnake.ui.Button(label='', emoji='⚠', style=disnake.ButtonStyle.gray, custom_id="report", disabled=True))

            bot = self.bot
            id = self.stats.find_one({'_id': inter.author.id})['last_comp']
            num = self.reports.find_one({'_id': "super"})['num']

            class MyModal(disnake.ui.Modal):
                def __init__(self):
                    # Детали модального окна и его компонентов
                    self.bot = bot
                    self.cluster = MongoClient(config.config["database"])
                    self.reports = self.cluster.AnonChat.reports
                    components = [
                        disnake.ui.TextInput(
                            label="Причина репорта",
                            placeholder="Оскорбления в мой адрес",
                            custom_id="Причина",
                            style=disnake.TextInputStyle.short,
                            max_length=250,
                            min_length=20
                        ),
                        disnake.ui.TextInput(
                            label="Ссылка на скрин с доказательством",
                            placeholder="htpps://...",
                            custom_id="Пруф",
                            style=disnake.TextInputStyle.short,
                            max_length=250,
                            min_length=10
                        )
                    ]
                    super().__init__(
                        title="Репорт",
                        custom_id="create_tag",
                        components=components,
                    )

                async def callback(self, interr: disnake.ModalInteraction):
                    desc = ''
                    link = ''
                    for key, value in interr.text_values.items():
                        if key.capitalize() == "Пруф":
                            link = value
                        else:
                            desc += ''.join(f'\n `{key.capitalize()}`: {value}')

                    emb = disnake.Embed(title="Репорт отправлен", description="Вы пожаловались на вашего собеседника, \nв скором времени с вами свяжутся для выяснения деталей.",
                                        color=disnake.Color.orange(), timestamp=datetime.datetime.now())
                    emb.set_footer(text=f"{interr.author.name}", icon_url=interr.author.avatar)

                    await interr.send(embed=emb)
                    embed = disnake.Embed(
                        title=f"Жалоба #{num + 1}",
                        description=desc,
                        color=disnake.Color.orange(),
                        timestamp=datetime.datetime.now())
                    embed.set_footer(text=f"Отправитель: {interr.author} | {interr.author.id}", icon_url=interr.author.avatar)
                    try:
                        embed.set_image(link)
                        await self.bot.get_guild(1103758994398523432).get_channel(1113516899070914620).send(embed=embed)
                    except:
                        embedd = disnake.Embed(
                            title=f"Жалоба #{num + 1}",
                            description=desc,
                            color=disnake.Color.orange(),
                            timestamp=datetime.datetime.now())
                        embedd.set_footer(text=f"Отправитель: {interr.author} | {interr.author.id}", icon_url=interr.author.avatar)
                        await self.bot.get_guild(1103758994398523432).get_channel(1113516899070914620).send(embed=embedd)
                    self.reports.update_one({"_id": "super"}, {"$set": {'num': num + 1}})
                    await inter.edit_original_response(view=buttons)
                    post = {
                        "_id": num + 1,
                        "user": id
                    }
                    self.reports.insert_one(post)

            await inter.response.send_modal(MyModal())

        elif inter.component.custom_id in ['btn1', 'btn2', "btn3"]:
            try:
                await inter.response.defer(ephemeral=True)
            except:
                pass

            captcha = self.captcha.find_one({"_id": inter.author.id})["captcha"]

            response = requests.post(
                url='https://api.boticord.top/v3/resources/ups/service/proceed',
                headers={
                    'Authorization': config.config['Boticord'],
                    'Content-type': 'application/json'
                },
                json={
                    "token": config.config['Boticord'],
                    "resource": "1078924878071214110",
                    "user": str(inter.author.id),
                    "captchaId": str(captcha),
                    "captchaAnswer": 0 if inter.component.custom_id == 'btn1' else 1 if inter.component.custom_id == 'btn2' else 2
                }
            )
            if response.status_code == 201:
                embed = disnake.Embed(title="Успешный ап", description="Вы апнули бота, спасибо!",
                                      color=disnake.Color.random(),
                                      timestamp=datetime.datetime.now())
                embed.set_thumbnail(inter.author.avatar)
                embed.set_footer(text=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")

                await inter.delete_original_message()
                await inter.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(title="Ошибка", description="Скорее всего вы выбрали неверный ответ.\n"
                                                                  "Если же это не так, попробуйте повторить попытку позже.",
                                      color=disnake.Color.random(),
                                      timestamp=datetime.datetime.now())
                embed.set_thumbnail(inter.author.avatar)
                embed.set_footer(text=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")

                await inter.delete_original_message()
                await inter.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Anon(bot))
