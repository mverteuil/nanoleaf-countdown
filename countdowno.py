from datetime import timedelta
import time

import click
import pytimeparse
from nanoleaf import Aurora

import configure

PANEL_STEPS = 60
STEP_SIZE = 255 // PANEL_STEPS


def reset_panels(panels, stream):
    for panel in panels:
        stream.panel_set(int(panel), white=0, red=0, green=0, blue=0, transition_time=0)


@click.argument("delay")
@click.command()
def main(delay):
    delay_seconds = pytimeparse.parse(delay)
    config = configure.get_or_create_config()
    panels = config["device"]["panel_order"].split(",")
    panel_count = len(panels)
    seconds_per_panel = delay_seconds // panel_count
    panel_step_size = seconds_per_panel / PANEL_STEPS
    device = Aurora(config["device"]["address"], config["device"]["token"])
    stream = device.effect_stream()

    reset_panels(panels, stream)

    for panel in panels:
        for index in range(0, PANEL_STEPS):
            index_offset = index + 1
            stream.panel_set(
                int(panel),
                white=1,
                transition_time=0,
                red=index_offset * STEP_SIZE,
                blue=0,
                green=0,
            )
            time.sleep(panel_step_size)


if __name__ == "__main__":
    main()
