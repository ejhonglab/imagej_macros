
import json
from os.path import join, exists

from ij import IJ, WindowManager


# TODO try to factor this out, to share w/ save_window_positions.py?
def window_position_json_path():
    # All the docs say about the preferences folder is that it is checked for
    # IJ_Prefs.txt, but it seems like a nice place to store window position/size
    # preferences.
    return join(IJ.getDirectory('preferences'), 'window_positions.json')


def main():
    window_pos_json_fname = window_position_json_path()

    #print 'window_pos_json_fname:', window_pos_json_fname

    if not exists(window_pos_json_fname):
        print window_pos_json_fname, 'did not exist! no positions to restore!'
        return

    with open(window_pos_json_fname, 'r') as f:
        # May raise ValueError if json is broken. Shouldn't keep happening though,
        # and--if it does--I need to deal with it.
        title2window_data = json.load(f)

    for title, json_window_data in title2window_data.items():
        window = WindowManager.getWindow(title)
        if window is None:
            print 'no window matching title:', title
            continue

        location = json_window_data['location']
        x, y = location
        #print 'x:', x, 'y:', y

        size = json_window_data['size']
        w, h = size
        #print 'w:', w, 'h:', h

        window.setLocationAndSize(x, y, w, h)

        # TODO ideally factor to share w/ getting code in save_window_positions
        new_location = window.getLocation()
        assert x == new_location.x and y == new_location.y

        new_size = window.getSize()
        assert w == new_size.width and h == new_size.height
        #


if __name__ == '__main__':
    main()


