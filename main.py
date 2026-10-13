from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import (
    RenderResultListAction,
)
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.CopyToClipboardAction import (
    CopyToClipboardAction,
)
from ulauncher.api.shared.action.ExtensionCustomAction import (
    ExtensionCustomAction,
)

import webcolors
import os
import json
import searcher

TEMP_ICON_DIR = "/tmp/ulauncher-colorer/"
CUSTOM_COLORS_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "custom_colors.json"
)


class ColorExtension(Extension):
    def __init__(self):
        super().__init__()

        if not os.path.exists(TEMP_ICON_DIR):
            os.mkdir(TEMP_ICON_DIR)

        if os.path.exists(CUSTOM_COLORS_JSON):
            with open(CUSTOM_COLORS_JSON, "r") as f:
                self.custom_colors = json.load(f)
        else:
            with open(CUSTOM_COLORS_JSON, "w") as f:
                f.write("{}")
            self.custom_colors = dict()

        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def set_custom_color(self, name, hex):
        self.custom_colors[name] = hex
        with open(CUSTOM_COLORS_JSON, "w") as f:
            json.dump(self.custom_colors, f)


def svg_template(hex):
    return f"""<svg width="128" height="128"><rect width="100%" height="100%" fill="#{hex}"/></svg>"""


def create_color_icon(hex: str):
    path = TEMP_ICON_DIR + hex + ".svg"

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(svg_template(hex))

    return path


def create_result_item(hex: str, name: str | None) -> ExtensionResultItem:
    icon_path = create_color_icon(hex)

    if name is None:
        text = hex
    else:
        text = f'{hex} ({name})'

    return ExtensionResultItem(
        icon=icon_path,
        name=text,
        description='enter to copy hex code',
        on_enter=CopyToClipboardAction(hex),
    )


def query_color(color: str, custom_colors=None):
    res = searcher.get_color(color, additional_colors=custom_colors)
    if res is None:
        return None

    return [create_result_item(hex, name) for hex, name in res]


class SetCommand:
    def __init__(self, name, hex):
        self.name = name
        self.hex = hex


class KeywordQueryEventListener(EventListener):
    def get_empty_result(self, text="enter query..."):
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/icon.png",
                    name=text,
                    on_enter=DoNothingAction(),
                )
            ]
        )

    def handle_command(self, query, extension):
        args = query.split()
        if len(args) == 0:
            return self.get_empty_result("enter command...")
        if args[0] == "set":
            if len(args) == 1:
                return self.get_empty_result("enter new color's name...")
            if len(args) == 2:
                return self.get_empty_result(f"enter {args[1]}'s hex value...")
            if len(args) > 3:
                return self.get_empty_result("too many arguments")

            action = ExtensionCustomAction(SetCommand(args[1], args[2]))

            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name=f"set {args[1]} to {args[2]}",
                        description="press enter to confirm",
                        on_enter=action,
                    )
                ]
            )

    def on_event(self, event, extension):
        query = event.get_argument()

        if not query:
            return self.get_empty_result()

        if query.startswith("!"):
            return self.handle_command(query[1:], extension)

        res = query_color(query, extension.custom_colors)

        if res is None:
            return self.get_empty_result()

        return RenderResultListAction(res)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, ext):
        data = event.get_data()

        if isinstance(data, SetCommand):
            ext.set_custom_color(data.name, data.hex)


if __name__ == "__main__":
    ColorExtension().run()
