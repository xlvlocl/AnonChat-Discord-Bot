import datetime
import disnake
from disnake import Option, OptionType
from disnake.ext import commands
from pymongo import MongoClient

import config


class Stuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = MongoClient(config.config["database"])
        self.collection = self.cluster.AnonChat.anon
        self.stats = self.cluster.AnonChat.stats
        self.guilds = self.cluster.AnonChat.guilds
        
    @commands.slash_command(name="stats", description="Покажет информацию об анонимном чате на этом сервере", dm_permission=False)
    async def stats(self, inter):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        guild = inter.guild
        people = self.collection.find()
        num = 0

        try:
            messages = self.guilds.find_one({"_id": guild.id})["messages"]
        except:
            messages = 0

        try:
            chats = self.guilds.find_one({"_id": guild.id})["chats"]
        except:
            chats = 0
        try:
            channel = await inter.guild.fetch_channel(self.guilds.find_one({'_id': inter.guild.id})["channel"])
        except:
            channel = None

        for i in people:
            if i["guild"] == guild.id:
                num += 1

        emb = disnake.Embed(title=f"Статистика {guild.name} в анонимном чате",
                            description="", colour=disnake.Color.random(), timestamp=datetime.datetime.now())
        emb.add_field(name='В анонимном чате:', value=f"`{num}` человек", inline=False)
        emb.add_field(name='Они написали:', value=f"`{messages}` сообщений", inline=False)
        emb.add_field(name='Поменяв при этом', value=f"`{chats}` собеседников", inline=False)
        emb.add_field(name='Канал с анонимным чатом', value=f'{"Не установлен" if channel is None else channel.mention}', inline=False)
        emb.set_thumbnail(url=guild.icon)
        emb.set_footer(text=f"{guild.name} ・ Вся статистика пишется только для этого сервера", icon_url=guild.icon)

        await inter.edit_original_message(embed=emb)

    @commands.slash_command(name="say", description="Пишет указанный текст в текущий канал или в другой указанный от лица бота", dm_permission=False,
                            options=[
                                Option("message", "Напишите сообщение", OptionType.string, required=True, max_length=300),
                                Option("channel", "Укажите канал для отправки", OptionType.channel, required=False),
                                Option("file", 'Добавить файл', OptionType.attachment, required=False)
                            ])
    async def say(self, inter: disnake.CommandInteraction, message, channel: disnake.TextChannel = None, file: disnake.Attachment = None):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass
        if channel is not None:
            if channel.permissions_for(inter.author).send_messages:
                if file is None:
                    await channel.send(message, allowed_mentions=disnake.AllowedMentions(roles=False, users=True, everyone=False))
                else:
                    file = await file.to_file()
                    await channel.send(message, allowed_mentions=disnake.AllowedMentions(roles=False, users=True, everyone=False), file=file)
                await inter.edit_original_message("Успешно отправлено!")
            else:
                await inter.edit_original_message(f"У вас недостаточно прав чтобы писать в канал {channel.mention}")
        else:
            if file is None:
                await inter.channel.send(message, allowed_mentions=disnake.AllowedMentions(roles=False, users=True, everyone=False))
            else:
                file = await file.to_file()
                await inter.channel.send(message, allowed_mentions=disnake.AllowedMentions(roles=False, users=True, everyone=False), file=file)
            await inter.edit_original_message("Успешно отправлено!")

    @commands.slash_command(name="avatar", description="Показывает ваш аватар если другой пользователь не указан", dm_permission=False,
                            options=[
                                Option("member", "Укажите пользователя", OptionType.user, required=False),
                            ])
    async def avatar(self, inter: disnake.CommandInteraction, member: disnake.Member = None):
        try:
            await inter.response.defer(ephemeral=True)
        except:
            pass

        if member is None:
            member = inter.author

        emb = disnake.Embed(title=f'Аватар {member.name}',
                            color=disnake.Color.random(),
                            timestamp=datetime.datetime.now())
        emb.set_image(member.avatar if member.avatar else member.default_avatar)
        await inter.send(embed=emb)

    # @commands.slash_command(name="shop", description="Показывает магазин с плюшками для анонимного чата", dm_permission=False)
    # async def shop(self, inter: disnake.CommandInteraction):
    #     try:
    #         await inter.response.defer(ephemeral=True)
    #     except:
    #         pass
    #
    #     class CreatePaginator(disnake.ui.View):
    #         def __init__(self, embedss: list, timeout=10):
    #             super().__init__(timeout=timeout)
    #             self.embeds = embedss
    #             self.CurrentEmbed = 0
    #             self.last_index = len(self.embeds) - 1
    #
    #         async def on_timeout(self):
    #             try:
    #                 await inter.delete_original_message()
    #             except:
    #                 pass
    #
    #         @disnake.ui.button(emoji="<a:2_:1067947438607958120>", style=disnake.ButtonStyle.grey)
    #         async def previous(self, button, inter):
    #             try:
    #                 if self.CurrentEmbed - 1 < 0:
    #                     self.CurrentEmbed = self.last_index
    #                 else:
    #                     self.CurrentEmbed -= 1
    #                 await inter.response.edit_message(embed=self.embeds[self.CurrentEmbed])
    #             except:
    #                 await inter.send('Не могу щёлкнуть страницу', ephemeral=True)
    #
    #         @disnake.ui.button(emoji="<a:1_:1067947382970535998>", style=disnake.ButtonStyle.grey)
    #         async def next(self, button, inter):
    #             try:
    #                 if self.CurrentEmbed + 1 > self.last_index:
    #                     self.CurrentEmbed = 0
    #                 else:
    #                     self.CurrentEmbed += 1
    #                 await inter.response.edit_message(embed=self.embeds[self.CurrentEmbed])
    #             except:
    #                 await inter.send('Не могу щёлкнуть страницу', ephemeral=True)
    #
    #     emb = disnake.Embed(title="Магазин", color=disnake.Color.random())
    #
    #     embedss = []
    #
    #     msg = await inter.send(embed=embedss[0], view=CreatePaginator(embedss, inter.author.id))


def setup(bot):
    bot.add_cog(Stuff(bot))
