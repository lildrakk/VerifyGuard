import discord
import json
import os
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "verificacion_config.json"

def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        config = {
            "rol_dar": 0,
            "rol_quitar": 0,
            "titulo": "Verificacion — VerifyGuard",
            "descripcion": "pulsa el boton de abajo para acceder a los demas canales"
        }
        guardar_config(config)
        return config

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


class BotonVerificacion(discord.ui.View):
    def __init__(self, rol_dar, rol_quitar):
        super().__init__(timeout=None)
        self.rol_dar = rol_dar
        self.rol_quitar = rol_quitar

        self.add_item(
            discord.ui.Button(
                label="Verificarme",
                emoji="✅",
                style=discord.ButtonStyle.primary,
                custom_id="verificar_usuario"
            )
        )

    @discord.ui.button(label="temp", style=discord.ButtonStyle.primary)
    async def callback_fake(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    async def interaction_check(self, interaction: discord.Interaction):
        rol_add = interaction.guild.get_role(self.rol_dar)
        rol_remove = interaction.guild.get_role(self.rol_quitar)

        if rol_remove in interaction.user.roles:
            await interaction.user.remove_roles(rol_remove)

        if rol_add not in interaction.user.roles:
            await interaction.user.add_roles(rol_add)

        await interaction.response.send_message(
            "verificacion completada", ephemeral=True
        )
        return True


class Verificacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verificacion", description="crear mensaje de verificacion y guardar configuracion")
    @app_commands.describe(
        rol_dar="rol que se dara al verificar",
        rol_quitar="rol que se quitara al verificar",
        titulo="titulo del embed",
        descripcion="descripcion del embed"
    )
    async def verificacion(
        self,
        interaction: discord.Interaction,
        rol_dar: discord.Role,
        rol_quitar: discord.Role,
        titulo: str,
        descripcion: str
    ):

        config = cargar_config()

        config["rol_dar"] = rol_dar.id
        config["rol_quitar"] = rol_quitar.id
        config["titulo"] = titulo
        config["descripcion"] = descripcion

        guardar_config(config)

        embed = discord.Embed(
            title=titulo,
            description=descripcion,
            color=discord.Color.blue()
        )

        view = BotonVerificacion(
            rol_dar.id,
            rol_quitar.id
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Verificacion(bot))
