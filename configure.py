import configparser
import time

import click
from nanoleaf.aurora import Aurora
from nanoleaf.setup import find_auroras, generate_auth_token


def get_or_create_config():
    """Get or create configuration, provisioning a new token for authenticated requests."""
    config = configparser.ConfigParser()
    config.read("countdowno.ini")
    if "device" in config:
        return config
    else:
        click.echo("Searching for Nanoleaf devices...")
        discovered_auroras = find_auroras()

        if discovered_auroras:
            config["device"]["address"] = discovered_auroras[0]
            click.echo(f"Found device at: {config['device_address']}")

            click.echo("Use the next 10 seconds to put the device in discovery mode...")
            time.sleep(10)

            click.echo("Attempting to provision authentication token...")
            config["device"]["token"] = generate_auth_token(config["device"]["address"])

            device = Aurora(config["device"]["address"], config["device"]["token"])
            panel_ids = [panel["panelId"] for panel in device.panel_positions]
            config["device"]["panel_order"] = panel_ids
            __write_config(config)
            return config
        else:
            click.secho("No devices discovered!", fg="red")


def __write_config(config):
    """Write configuration file to disk."""
    config.write("countdowno.ini")


def display_panel_ordering(config, new_ordering):
    """Progressively display light on panels using the new id ordering."""
    saved_ordering = config["device"]["panel_order"]
    new_ordering = new_ordering.split(",")

    panel_count = len(saved_ordering)
    assert (
        len(new_ordering) == panel_count
    ), f"Missing some panel ids, expected all of the following: {saved_ordering}"

    device = Aurora(config["device"]["address"], config["device"]["token"])
    stream = device.effect_stream()

    step_size = 255 // panel_count
    for index, panel_id in enumerate(new_ordering, start=1):
        stream.panel_set(
            panel_id, red=step_size * index, green=0, blue=0, transition_time=0
        )
        time.sleep(0.2)


@click.option("--new-ordering", default=None)
@click.command()
def main(new_ordering):
    config = get_or_create_config()
    ordering = new_ordering or config["device"]["panel_order"]
    display_panel_ordering(config, ordering)


if __name__ == "__main__":
    main()
