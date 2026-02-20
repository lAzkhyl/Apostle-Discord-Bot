import discord
from modules.vouch.db import vouch_db
from modules.vouch.views.helpers import send_log


class ConfirmRevokeView(discord.ui.View):

    def __init__(self, code: str, used_by: int | None, role_id: int):
        super().__init__(timeout=120)
        self.code = code
        self.used_by = used_by
        self.role_id = role_id

    @discord.ui.button(
        label="Confirm Revoke",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
    )
    async def confirm_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.defer()
        await vouch_db.execute_revoke(self.code)

        log_lines = [
            f"Code `{self.code}` revoked by {interaction.user.mention}."
        ]

        if self.used_by:
            member = interaction.guild.get_member(self.used_by)
            role = interaction.guild.get_role(self.role_id)

            if member and role:
                try:
                    await member.remove_roles(
                        role,
                        reason=f"Vouch revoked by {interaction.user.name}",
                    )
                    dm_embed = discord.Embed(
                        title="⚠️  Vouch Revoked",
                        description=(
                            f"Your access via voucher code `{self.code}` has been revoked "
                            f"by the code creator. Role **{role.name}** has been removed."
                        ),
                        color=discord.Color.red(),
                    )
                    await member.send(embed=dm_embed)
                    log_lines.append(
                        f"Role {role.mention} removed from {member.mention}."
                    )
                except (discord.Forbidden, discord.HTTPException):
                    log_lines.append(
                        "⚠️ Failed to remove role or send DM to user."
                    )
        result_embed = discord.Embed(
            title="✅  Revoke Successful",
            description="\n".join(log_lines),
            color=discord.Color.red(),
        )

        for child in self.children:
            child.disabled = True

        await interaction.edit_original_response(embed=result_embed, view=self)

        log_embed = discord.Embed(
            title="🗑️  Vouch Revoked",
            description="\n".join(log_lines),
            color=discord.Color.red(),
        )
        await send_log(interaction.guild, log_embed)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        emoji="✖️",
    )
    async def cancel_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            content="Revoke cancelled.",
            embed=None,
            view=None,
        )


class ManageVouchSelect(discord.ui.Select):
    """
    Dropdown untuk memilih kode vouch yang ingin dikelola.
    Menampilkan status tiap kode dengan emoji indikator.
    """

    STATUS_EMOJI = {
        "ACTIVE":  "🟢",
        "USED":    "🔴",
        "REVOKED": "⚫",
        "EXPIRED": "🟡",
    }

    def __init__(self, vouches: list):
        # Simpan sebagai dict untuk akses cepat
        self.vouch_dict = {row[0]: row for row in vouches}

        options = [
            discord.SelectOption(
                label=row[0],
                description=f"Status: {row[1]}",
                value=row[0],
                emoji=self.STATUS_EMOJI.get(row[1], "⚪"),
            )
            for row in vouches
        ]

        super().__init__(
            placeholder="Pilih kode vouch untuk dikelola...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_code = self.values[0]
        code, status, created_at, used_by, role_id = self.vouch_dict[selected_code]

        detail_embed = discord.Embed(
            title="📋  Vouch Code Details",
            color=discord.Color.blue(),
        )
        detail_embed.add_field(name="Code",    value=f"`{code}`",                    inline=False)
        detail_embed.add_field(name="Status",  value=status,                         inline=True)
        detail_embed.add_field(name="Created", value=str(created_at).split(".")[0],  inline=True)

        if used_by:
            detail_embed.add_field(
                name="Used By",
                value=f"<@{used_by}>",
                inline=False,
            )

        # Tentukan apakah kode masih bisa di-revoke
        if status in ("ACTIVE", "USED"):
            if status == "USED":
                detail_embed.description = (
                    "⚠️ **Peringatan:** Kode ini sudah digunakan. "
                    "Mencabut kode akan **menghapus role** dari pemakainya dan mengirim notifikasi DM."
                )
                revoke_view = ConfirmRevokeView(code, used_by, role_id)
            else:
                detail_embed.description = "Apakah kamu yakin ingin mencabut kode ini?"
                revoke_view = ConfirmRevokeView(code, None, role_id)

            await interaction.response.edit_message(embed=detail_embed, view=revoke_view)
        else:
            detail_embed.description = (
                f"Kode ini berstatus **{status}** dan tidak dapat dimodifikasi."
            )
            await interaction.response.edit_message(embed=detail_embed, view=None)


class ManageVouchView(discord.ui.View):
    """Wrapper View yang menampung ManageVouchSelect."""

    def __init__(self, vouches: list):
        super().__init__(timeout=120)
        self.add_item(ManageVouchSelect(vouches))
