import discord
from discord import app_commands
from discord.ext import commands

from modules.profile.service import ProfileService
from modules.profile.views import ProfileView


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="profile",
        description="View your server profile and reputation",
    )
    @app_commands.guild_only()
    async def user_profile(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None,
    ):
        target = member or interaction.user
        is_self = target.id == interaction.user.id

        await interaction.response.defer()

        profile_embed = await ProfileService.build_embed(target, interaction.guild)

        await interaction.followup.send(
            embed=profile_embed,
            view=ProfileView(target=target, is_self=is_self),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
