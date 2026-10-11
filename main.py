from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

import webcolors
import os
import json

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


def query_color(color: str, custom_colors=None):
    res = get_hex(color, custom_colors)
    if res is None:
        return None

    hex, is_name = res

    if is_name:
        name = f"#{hex} ({color})"
    else:
        name = f"#{hex}"

    path = create_color_icon(hex)

    return hex, name, path


def get_hex(color: str, custom_colors=None) -> tuple[str, bool] | None:
    if color is None or len(color.strip()) == 0:
        return None

    is_name = False

    if custom_colors is not None and color in custom_colors:
        return custom_colors[color], True

    try:
        c = webcolors.normalize_hex(color)
    except ValueError:
        try:
            c = webcolors.normalize_hex("#" + color)
        except ValueError:
            try:
                c = webcolors.name_to_hex(color)
                is_name = True
            except ValueError:
                return None

    return c[1:], is_name


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

        hex, name, path = res

        items = [
            ExtensionResultItem(
                icon=path,
                name=name,
                description="enter to copy hex",
                on_enter=CopyToClipboardAction(hex),
            )
        ]

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, ext):
        data = event.get_data()

        if isinstance(data, SetCommand):
            ext.set_custom_color(data.name, data.hex)


if __name__ == "__main__":
    ColorExtension().run()
