import discord
from modules.vouch.views.modals import ChangeNickModal


class FirstTimeRedeemView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Set Nickname (Optional)",
        style=discord.ButtonStyle.primary,
        emoji="✏️",
        custom_id="first_time_btn_change_nick",
    )
    async def change_nick_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_modal(ChangeNickModal())
