import discord
from discord.ext import commands
from discord import app_commands

class ComandosBasicos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # MUTE
    @app_commands.command(name="mute", description="silenciar a un usuario")
    @app_commands.describe(
        usuario="usuario que sera silenciado",
        razon="razon del mute"
    )
    async def mute(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "no especificada"):
        rol_mute = discord.utils.get(interaction.guild.roles, name="Muted")

        if rol_mute is None:
            return await interaction.response.send_message("no existe el rol Muted", ephemeral=True)

        await usuario.add_roles(rol_mute, reason=razon)
        await interaction.response.send_message(f"{usuario.mention} ha sido muteado por {razon}")

    # UNMUTE
    @app_commands.command(name="unmute", description="quitar mute a un usuario")
    @app_commands.describe(
        usuario="usuario al que se le quitara el mute"
    )
    async def unmute(self, interaction: discord.Interaction, usuario: discord.Member):
        rol_mute = discord.utils.get(interaction.guild.roles, name="Muted")

        if rol_mute is None:
            return await interaction.response.send_message("no existe el rol Muted", ephemeral=True)

        await usuario.remove_roles(rol_mute)
        await interaction.response.send_message(f"{usuario.mention} ya no esta muteado")

    # KICK
    @app_commands.command(name="kick", description="expulsar a un usuario del servidor")
    @app_commands.describe(
        usuario="usuario que sera expulsado",
        razon="razon del kick"
    )
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "no especificada"):
        await usuario.kick(reason=razon)
        await interaction.response.send_message(f"{usuario.mention} ha sido expulsado por {razon}")

    # BAN
    @app_commands.command(name="ban", description="banear a un usuario del servidor")
    @app_commands.describe(
        usuario="usuario que sera baneado",
        razon="razon del ban"
    )
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "no especificada"):
        await usuario.ban(reason=razon)
        await interaction.response.send_message(f"{usuario.mention} ha sido baneado por {razon}")

    # UNBAN
    @app_commands.command(name="unban", description="desbanear a un usuario")
    @app_commands.describe(
        usuario="nombre y tag del usuario ejemplo: nombre#0000"
    )
    async def unban(self, interaction: discord.Interaction, usuario: str):
        nombre, tag = usuario.split("#")
        for ban in await interaction.guild.bans():
            if ban.user.name == nombre and ban.user.discriminator == tag:
                await interaction.guild.unban(ban.user)
                return await interaction.response.send_message(f"{ban.user} ha sido desbaneado")

        await interaction.response.send_message("no se encontro ese usuario en la lista de bans", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ComandosBasicos(bot))
