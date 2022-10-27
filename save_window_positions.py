
from os.path import join, exists
import json

from ij import IJ, WindowManager


# TODO try to factor this out. copied from restore_window_positions.py
def window_position_json_path():
    return join(IJ.getDirectory('preferences'), 'window_positions.json')


def main():
    verbose = False

    window_pos_json_fname = window_position_json_path()

    print 'writing window position/sizes to', window_pos_json_fname

    # TODO maybe add to any existing data, only overwriting the titles we have here?

    # getNonImageTitles seems to return titles for things more like what
    # getAllNonImageWindows returns, rather than getNonImageWindows, if it matters
    titles = WindowManager.getImageTitles() + WindowManager.getNonImageTitles()

    title2window_data = dict()
    for title in WindowManager.getImageTitles():
        window = WindowManager.getWindow(title)
        if verbose:
            print 'title:', title
            print 'location:', window.getLocation()
            print 'size (via java.awt.Component):', window.getSize()
            print ''

        location = window.getLocation()
        size = window.getSize()

        title2window_data[title] = {
            'location': (location.x, location.y),
            'size': (size.width, size.height),
        }

    with open(window_pos_json_fname, 'w') as f:
        json.dump(title2window_data, f)

    # TODO possible to flush? need to wait some amount of time for writing to finish?
    # not sure why i got a seemingly truncated json...


if __name__ == '__main__':
    main()


