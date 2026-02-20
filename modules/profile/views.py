import discord
from modules.profile.service import ProfileService


class ProfileView(discord.ui.View):

    def __init__(self, target: discord.Member, is_self: bool):
        super().__init__(timeout=180)
        self.target = target
        self.is_self = is_self

        if not is_self:
            self.extended_button.label = "Extended Info (Owner Only)"
            self.extended_button.style = discord.ButtonStyle.secondary

    @discord.ui.button(
        label="Extended Info",
        style=discord.ButtonStyle.primary,
        emoji="🔐",
        custom_id="profile_btn_extended",
    )
    async def extended_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(
                content=(
                    "❌ **Access Denied**\n"
                    "Extended information can only be accessed by the profile owner."
                ),
                ephemeral=True,
            )
            return

        extended_embed = ProfileService.build_extended_embed(self.target)

        await interaction.response.send_message(
            embed=extended_embed,
            ephemeral=True,
        )


class ProfileConfirmPostView(discord.ui.View):

    def __init__(self, target: discord.Member):
        super().__init__(timeout=60)
        self.target = target

    @discord.ui.button(
        label="Post to Channel",
        style=discord.ButtonStyle.success,
        emoji="📢",
    )
    async def confirm_post(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        profile_embed = await ProfileService.build_embed(
            self.target,
            interaction.guild,
        )

        await interaction.channel.send(
            embed=profile_embed,
            view=ProfileView(target=self.target, is_self=True),
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="✅ **Profile successfully posted to channel.**",
            view=self,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        emoji="✖️",
    )
    async def cancel_post(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            content="Profile was not posted.",
            embed=None,
            view=None,
        )
