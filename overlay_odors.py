
# Will remove any existing overlay

import json
from os.path import split, join, exists

from ij import IJ
from ij.gui import Overlay, TextRoi
from java.awt import Color


# TODO TODO TODO add hotkeys (via a separate script, or maybe diff args to this one?)
# to jump to first frame of next / prev odor

# TODO maybe set at least the very last frame to have no overlay, at least for
# non-concat movies, so when we are comparing one that is and isn't, it's clear the odor
# info has run off the end for the shorter movie, when we are syncing t-frames and are
# looking at further frames in the concatenated movie?

def overlay(imp=None):

    verbose = False

    if imp is None:
        imp = IJ.getImage()

    file_info = imp.getOriginalFileInfo()
    abs_tiff_path = file_info.getFilePath()
    tiff_dir = split(abs_tiff_path)[0]

    json_fname = join(tiff_dir, 'trial_frames_and_odors.json')
    if not exists(json_fname):
        print 'odor / frame info did not exist at:', json_fname
        print 'doing nothing!'
        return

    n_frames = imp.getNFrames()
    if n_frames <= 1:
        print 'current image does not have more than one frame! doing nothing!'
        return

    with open(json_fname, 'r') as f:
        trial_data_list = json.load(f)

    # TODO TODO err if n_frames doesn't match up w/ # timepoints in movie
    # TODO err if any frames are overlapping (/ missing)

    if verbose:
        from pprint import pprint
        pprint(trial_data_list)
        print ''

    text_x_pos = 10
    text_y_pos = 12

    # TextRoi.getDefaultFontSize(): 18
    font_size = 8

    # Default color: java.awt.Color(255, 255, 0) (r=255, g=255, b=0)
    default_color = Color(255, 255, 0)
    first_odor_frame_color = Color(255, 0, 0)

    overlay = Overlay()

    for trial_data in trial_data_list:
        start_frame = trial_data['start_frame'] + 1
        first_odor_frame = trial_data['first_odor_frame'] + 1
        end_frame = trial_data['end_frame'] + 1

        # str describing all odors presented on this trial
        odors = trial_data['odors']

        # TODO decrease font size in general (to deal w/ long strings corresponding to
        # mixtures of two odors, but also in general). maybe use
        # TextRoi.setDefaultFontSize? or one of the other constructors where you also
        # manaully pass in a java.awt.Font?
        # https://imagej.nih.gov/ij/developer/api/ij/ij/gui/TextRoi.html
        # TODO or just <text roi>.setFontsize(int size)?

        # TODO TODO do something with first_odor_frame (change color during odor pulse?
        # would need info about end...) (could at least do on first frame...)
        # TODO or maybe show a separate overlay component when odor is on (e.g. dot)?
        for t in range(start_frame, end_frame + 1):
            roi = TextRoi(text_x_pos, text_y_pos, odors)
            roi.setPosition(0, 0, t)

            if t != first_odor_frame:
                roi.setColor(default_color)

            # TODO TODO TODO need to encode a global frame duration (of odor
            # presentation) somewhere, or maybe just have add a last_odor_frame, for
            # same reason it made sense to have this rather than a global frame offset
            # anyway...
            else:
                # TODO TODO TODO why is this not working? (this else branch *is* being
                # reached)
                roi.setColor(first_odor_frame_color)

            roi.setFontSize(font_size)

            overlay.add(roi)

    imp.setOverlay(overlay)
    imp.show()


if __name__ == '__main__':
    overlay()

