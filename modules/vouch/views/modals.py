import discord
from modules.vouch.db import vouch_db
from modules.vouch.views.helpers import send_log


class RedeemModal(discord.ui.Modal, title="🎟️  Redeem Vouch Code"):

    code_input = discord.ui.TextInput(
        label="Vouch Code",
        placeholder="Example: V-ABCD-EFGH-IJKL",
        required=True,
        max_length=50,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        code = self.code_input.value.strip().upper()
        success, role_id, is_first_time, message = await vouch_db.redeem_vouch(
            code, interaction.user.id
        )

        if not success:
            error_embed = discord.Embed(
                title="❌  Redemption Failed",
                description=f"**Reason:** {message}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.followup.send(
                content="⚠️ Role rewards are no longer available on this server. Please contact the Administrator.",
                ephemeral=True,
            )
            return

        try:
            await interaction.user.add_roles(
                role, reason=f"Vouch Redeem: {code}"
            )
        except discord.Forbidden:
            await interaction.followup.send(
                content="⚠️ The bot does not have permission to grant this role. Please contact the Administrator.",
                ephemeral=True,
            )
            return

        if is_first_time:
            from modules.vouch.views.first_time_view import FirstTimeRedeemView
            welcome_embed = discord.Embed(
                title="🎉  Welcome to Two Moon!",
                description=(
                    f"Vouch code successfully redeemed!\n"
                    f"Role **{role.name}** has been granted to you.\n\n"
                    f"As a new member, you can set your nickname here."
                ),
                color=discord.Color.gold(),
            )
            await interaction.followup.send(
                embed=welcome_embed,
                view=FirstTimeRedeemView(),
                ephemeral=True,
            )
        else:
            success_embed = discord.Embed(
                title="✅  Vouch Redeemed",
                description=f"Role **{role.name}** has been successfully granted.",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

        # ── Kirim log ke channel admin ────────────────────────
        log_embed = discord.Embed(title="📥  Vouch Redeemed", color=discord.Color.green())
        log_embed.add_field(name="User",  value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Code",  value=f"`{code}`",              inline=True)
        log_embed.add_field(name="Role",  value=role.mention,             inline=True)
        await send_log(interaction.guild, log_embed)


class ChangeNickModal(discord.ui.Modal, title="✏️  Set Server Nickname"):

    nickname = discord.ui.TextInput(
        label="New Nickname",
        placeholder="Enter the nickname you'd like...",
        required=True,
        max_length=32,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_nick = self.nickname.value.strip()
        try:
            await interaction.user.edit(nick=new_nick)
            await interaction.response.send_message(
                content=f"✅ Nickname successfully changed to **{new_nick}**!",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                content="⚠️ The bot does not have permission to change your nickname.",
                ephemeral=True,
            )
