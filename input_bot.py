from __future__ import annotations

import asyncio
import os
from enum import auto, Enum, unique

import discord
from dotenv import load_dotenv
from pyboy import PyBoy, WindowEvent


@unique
class GameAction(Enum):
    LEFT = WindowEvent.PRESS_ARROW_LEFT, WindowEvent.RELEASE_ARROW_LEFT
    RIGHT = WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.RELEASE_ARROW_RIGHT
    UP = WindowEvent.PRESS_ARROW_UP, WindowEvent.RELEASE_ARROW_UP
    DOWN = WindowEvent.PRESS_ARROW_DOWN, WindowEvent.RELEASE_ARROW_DOWN
    START = WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START
    SELECT = WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT
    A = WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A
    B = WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B
    LOAD = auto()
    QUIT = auto()
    EXIT = auto()
    KILL = auto()
    INVALID = auto()

    @classmethod
    def from_message_content(cls, text: str) -> GameAction:
        if text == 'left' or text == '<':
            return cls.LEFT
        elif text == 'right' or text == '>':
            return cls.RIGHT
        elif text == 'down' or text == 'v':
            return cls.DOWN
        elif text == 'up' or text == '^':
            return cls.UP
        elif text == 'start':
            return cls.START
        elif text == 'select':
            return cls.SELECT
        elif text == 'a':
            return cls.A
        elif text == 'b':
            return cls.B
        elif text  == 'load':
            return cls.LOAD
        elif text == 'quit':
            return cls.QUIT
        elif text == 'exit':
            return cls.EXIT
        elif text == 'kill':
            return cls.KILL
        else:
            return cls.INVALID


class PyBoyInputDaemon(PyBoy):
    FPS = 60

    def __init__(self: PyBoyInputDaemon):
        self.buffer = []
        self.running = False

    def _get_save_filename(filename: str) -> str:
        return filename + '.state'

    def load(self, gamerom_file: str, *args, **kwargs):
        super().__init__(gamerom_file, *args, **kwargs)
        save_filename = PyBoyInputDaemon._get_save_filename(gamerom_file)
        if os.path.exists(save_filename):
            with open(save_filename, 'rb') as state_file:
                self.load_state(state_file)

    async def loop(self: PyBoyInputDaemon):
        self.running = True
        while True:
            if self.buffer:
                self.send_input(self.buffer.pop())
            if self.tick():
                break
            await asyncio.sleep(1 / self.FPS)
        self.running = False

    def buffer_press_and_release(self: PyBoyInputDaemon, button_press: int, button_release: int):
        self.buffer.append(button_press)
        self.buffer.append(button_release)

    def stop(self, save=True):
        super().stop(save)

    def quit(self: PyBoyInputDaemon):
        save_filename = PyBoyInputDaemon._get_save_filename(self.gamerom_file)
        with open(save_filename, 'wb') as state_file:
            self.save_state(state_file)
        self.stop()

    def exit(self: PyBoyInputDaemon):
        self.stop(save=False)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')
ROM_FOLDER = os.getenv('ROM_FOLDER')
ROM_FILE = os.getenv('ROM_FILE')
rom_path = os.path.join(ROM_FOLDER, ROM_FILE)

client = discord.Client()
input_daemon = PyBoyInputDaemon()


@client.event
async def on_message(message: discord.Message):
    guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    if message.guild.id != guild.id or message.channel.name != CHANNEL:
        return
    text = message.content.lower()
    await message.delete()
    action = GameAction.from_message_content(text)
    if action is GameAction.KILL:
        if input_daemon.running:
            input_daemon.quit()
        exit()
    if action is GameAction.LOAD:
        if not input_daemon.running:
            input_daemon.load(rom_path)
            await input_daemon.loop()
    elif input_daemon.running:
        if action is GameAction.QUIT:
            input_daemon.quit()
        elif action is GameAction.EXIT:
            input_daemon.exit()
        elif action is not GameAction.INVALID:
            input_daemon.buffer_press_and_release(*action.value)


client.run(TOKEN)
