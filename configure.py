import configparser
import time

import bokeh
import click
import sys
from bokeh import plotting
from bokeh.models.glyphs import Text
from nanoleaf.aurora import Aurora

from aurora_setup import find_auroras, generate_auth_token

PLOT_OUTPUT = "plot.html"


def get_or_create_config():
    """Get or create configuration, provisioning a new token for authenticated requests."""
    config = configparser.ConfigParser()
    config.read("countdowno.ini")
    if "device" in config:
        return config
    else:
        click.echo("Searching for Nanoleaf devices...")
        discovered_auroras = find_auroras(seek_time=10)

        if discovered_auroras:
            config["device"] = {}
            config["device"]["address"] = discovered_auroras[0]

            click.echo(f"Auto selected device: {config['device']['address']}")

            click.echo("Use the next 10 seconds to put the device in discovery mode...")
            time.sleep(10)

            click.echo("Attempting to provision authentication token...")
            config["device"]["token"] = generate_auth_token(config["device"]["address"])

            device = Aurora(config["device"]["address"], config["device"]["token"])
            panel_ids = [panel["panelId"] for panel in device.panel_positions]
            config["device"]["panel_order"] = ",".join(
                str(panel_id) for panel_id in panel_ids
            )
            __write_config(config)
            return config
        else:
            click.secho("No devices discovered!", fg="red")


def __write_config(config):
    """Write configuration file to disk."""
    config.write(open("countdowno.ini", "w"))


def display_panel_ordering(config, new_ordering):
    """Progressively display light on panels using the new id ordering."""
    saved_ordering = config["device"]["panel_order"].split(",")
    panel_count = len(saved_ordering)
    assert not (
        set(new_ordering).difference(saved_ordering)
    ), f"Missing some panel ids, expected all of the following: {saved_ordering}"

    device = Aurora(config["device"]["address"], config["device"]["token"])
    stream = device.effect_stream()

    step_size = 255 // panel_count
    for index, panel_id in enumerate(new_ordering, start=1):
        stream.panel_set(
            int(panel_id),
            red=step_size * index,
            green=0,
            blue=0,
            white=1,
            transition_time=0,
        )
        time.sleep(0.2)


def plot_panel_positions(config):
    device = Aurora(config["device"]["address"], config["device"]["token"])

    x_values = []
    y_values = []
    ids = []
    angles = []

    for panel in device.panel_positions:
        x_values.append(panel["x"])
        y_values.append(panel["y"])
        ids.append(panel["panelId"])
        angles.append(panel["o"])

    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    x_padding = (x_max - x_min) * 0.1
    y_padding = (y_max - y_min) * 0.1

    plotting.output_file(PLOT_OUTPUT)
    plot = plotting.figure(
        x_range=(x_min - x_padding, x_max + x_padding),
        y_range=(y_min - y_padding, y_max + y_padding),
    )
    source = bokeh.models.ColumnDataSource(dict(x=x_values, y=y_values, text=ids))
    plot.triangle(
        x_values,
        y_values,
        angle=angles,
        angle_units="deg",
        size=70,
        color="#cccccc",
        fill_color=None,
        line_width=4,
    )
    glyph = bokeh.models.glyphs.Text(
        x="x", y="y", text="text", angle=0, text_align="center", text_color="#FF0000"
    )
    plot.add_glyph(source, glyph)
    plotting.show(plot)


@click.option("--new-ordering", default=None)
@click.option("--plot-ordering", default=False)
@click.command()
def main(new_ordering, plot_ordering):
    config = get_or_create_config()
    if plot_ordering:
        plot_panel_positions(config)
    else:
        # Order arrives LTR, but is stored in reverse
        new_ordering = list(reversed(new_ordering.split(",")))
        ordering = new_ordering or config["device"]["panel_order"]
        try:
            display_panel_ordering(config, ordering)
        except:
            sys.exit(1)
        else:
            config["device"]["panel_order"] = ",".join(new_ordering)
            __write_config(config)
            click.echo("Saved new ordering.")


if __name__ == "__main__":
    main()
