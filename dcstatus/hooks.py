"""Event Hooks"""

import os
from argparse import Namespace

from cachelib import FileSystemCache, NullCache
from deltabot_cli import BotCli
from deltachat2 import Bot, ChatType, CoreEvent, EventType, MsgData, NewMsgEvent, events
from rich.logging import RichHandler

from .status import get_status

cli = BotCli("dcstatus")
cli.add_generic_option(
    "--no-time",
    help="do not display date timestamp in log messages",
    action="store_false",
)
cache = NullCache()


@cli.on_init
def on_init(bot: Bot, args: Namespace) -> None:
    bot.logger.handlers = [
        RichHandler(show_path=False, omit_repeated_times=False, show_time=args.no_time)
    ]
    for accid in bot.rpc.get_all_account_ids():
        if not bot.rpc.get_config(accid, "displayname"):
            bot.rpc.set_config(accid, "displayname", "Delta Chat Status")
            status = "I'm a bot, send /help to me for more info"
            bot.rpc.set_config(accid, "selfstatus", status)
            bot.rpc.set_config(accid, "delete_device_after", "3600")


@cli.on_start
def on_start(_bot: Bot, args: Namespace) -> None:
    global cache
    path = os.path.join(args.config_dir, "cache")
    if not os.path.exists(path):
        os.makedirs(path)
    cache = FileSystemCache(path, default_timeout=60 * 60 * 3)


@cli.on(events.RawEvent)
def log_event(bot: Bot, accid: int, event: CoreEvent) -> None:
    if event.kind == EventType.INFO:
        bot.logger.debug(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)
    elif event.kind == EventType.MSG_DELIVERED:
        bot.rpc.delete_messages(accid, [event.msg_id])
    elif event.kind == EventType.SECUREJOIN_INVITER_PROGRESS:
        if event.progress == 1000 and not is_bot(bot, accid, event.contact_id):
            bot.logger.debug("QR scanned by contact id=%s", event.contact_id)
            chatid = bot.rpc.create_chat_by_contact_id(accid, event.contact_id)
            send_help(bot, accid, chatid)


@cli.on(events.NewMessage(command="/help"))
def _help(bot: Bot, accid: int, event: NewMsgEvent) -> None:
    bot.rpc.markseen_msgs(accid, [event.msg.id])
    send_help(bot, accid, event.msg.chat_id)


@cli.on(events.NewMessage(command="/status"))
def _status(bot: Bot, accid: int, event: NewMsgEvent) -> None:
    bot.rpc.markseen_msgs(accid, [event.msg.id])
    text = "Delta Chat releases status 🚀"
    html = get_status(cache, bot.logger)
    bot.rpc.send_msg(accid, event.msg.chat_id, MsgData(text=text, html=html))


@cli.on(events.NewMessage(is_info=False))
def on_message(bot: Bot, accid: int, event: NewMsgEvent) -> None:
    if bot.has_command(event.command):
        return

    msg = event.msg
    chat = bot.rpc.get_basic_chat_info(accid, msg.chat_id)
    if chat.chat_type == ChatType.SINGLE:
        bot.rpc.markseen_msgs(accid, [msg.id])
        send_help(bot, accid, event.msg.chat_id)


@cli.after(events.NewMessage)
def delete_msgs(bot, accid, event):
    bot.rpc.delete_messages(accid, [event.msg.id])


def send_help(bot: Bot, accid: int, chatid: int) -> None:
    text = (
        "👋 hi, I'm a bot, you can send /status to me"
        " to get the status of Delta Chat releases."
    )
    bot.rpc.send_msg(accid, chatid, MsgData(text=text))


def is_bot(bot: Bot, accid: int, contactid: int) -> bool:
    return bot.rpc.get_contact(accid, contactid).is_bot


if __name__ == "__main__":
    try:
        cli.start()
    except KeyboardInterrupt:
        pass
