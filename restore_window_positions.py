
import json
from os.path import join, exists

from ij import IJ, WindowManager


verbose = False

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

        old_location = window.getLocation()
        old_size = window.getSize()

        window.setLocationAndSize(x, y, w, h)

        if verbose:
            # TODO ideally factor to share w/ getting code in save_window_positions
            new_location = window.getLocation()
            if not (x == new_location.x and y == new_location.y):
                print 'did not succesfully set position!'
                print 'old: x=%d y=%d' % (old_location.x, old_location.y)
                print 'new: x=%d y=%d' % (new_location.x, new_location.y)
                print 'target: x=%d y=%d' % (x, y)
                print ''


            new_size = window.getSize()
            if not (w == new_size.width and h == new_size.height):
                print 'did not succesfully set size!'
                print 'old: width=%d height=%d' % (old_size.width, old_size.height)
                print 'new: width=%d height=%d' % (new_size.width, new_size.height)
                print 'target: width=%d height=%d' % (w, h)
                print ''

        # TODO fix if possible. maybe just need to allow time for it to resize or
        # something? for some reason i can't readily reproduce this (loading same data
        # via F2 twice consecutively, and w/ the only call to this happening inside the
        # open_experiment_and_rois.py call)
        #assert w == new_size.width and h == new_size.height
        #


if __name__ == '__main__':
    main()


