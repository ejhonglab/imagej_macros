
# Will remove any existing overlay

import json
from os.path import split, join, exists

from ij import IJ
from ij.gui import Overlay, TextRoi
from java.awt import Color


# TODO add hotkeys (via a separate script, or maybe diff args to this one?) to jump to
# first frame of next / prev odor? less important now that i mainly use tiffs processed
# so time dimension has one odor per time point

# TODO maybe set at least the very last frame to have no overlay, at least for
# non-concat movies, so when we are comparing one that is and isn't, it's clear the odor
# info has run off the end for the shorter movie, when we are syncing t-frames and are
# looking at further frames in the concatenated movie?

# TODO TODO factor out fn for getting odor from time index + odor list?

def overlay(imp=None):

    verbose = False

    if imp is None:
        imp = IJ.getImage()

    file_info = imp.getOriginalFileInfo()
    # TODO can i just do file_info.directory as in overlay_rois_in_curr_z.py? diffs?
    abs_tiff_path = file_info.getFilePath()
    tiff_dir = split(abs_tiff_path)[0]

    n_frames = imp.getNFrames()
    if n_frames <= 1:
        print 'current image does not have more than one frame! doing nothing!'
        return

    json_fname = join(tiff_dir, 'trial_frames_and_odors.json')
    if verbose:
        print 'odor/frame json:', json_fname

    if not exists(json_fname):
        print 'odor / frame info did not exist at:', json_fname
        print 'doing nothing!'
        return

    with open(json_fname, 'r') as f:
        trial_data_list = json.load(f)

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


    # TODO compute # of consecutive repeats, rather than assuming it is 3.
    # port my existing code that does this.
    n_repeats = 3

    # (for sam's use case where some odors only have 1 trial each, in same flies as
    # other experiments w/ usual 3 trials per odor)
    no_seq_dupes = []
    for x in trial_data_list:
        # assuming that if x['odors'] matches that of last, the rest of the relevant
        # data will too (should almost always be true. includes conc.)
        if len(no_seq_dupes) == 0 or x['odors'] != no_seq_dupes[-1]['odors']:
            no_seq_dupes.append(x)

    trial_data_iter = trial_data_list

    if len(trial_data_list) == n_frames:
        tiff_frames_are = 'presentations'

    # TODO delete?
    #elif len(trial_data_list) // n_repeats == n_frames:
    elif len(no_seq_dupes) == n_frames:
        tiff_frames_are = 'trial-averaged-odors'
        trial_data_iter = no_seq_dupes

    else:
        # TODO instead of this assertion, just do nothing and say why
        #assert n_frames > len(trial_data_list)
        tiff_frames_are = 'time'
        # TODO TODO err (/log to console / popup warning) if n_frames doesn't match up
        # w/ # timepoints in movie
        # TODO err if any frames are overlapping (/ missing)

    for i, trial_data in enumerate(trial_data_iter):
        if tiff_frames_are == 'time':
            start_frame = trial_data['start_frame'] + 1
            first_odor_frame = trial_data['first_odor_frame'] + 1
            end_frame = trial_data['end_frame'] + 1

        elif tiff_frames_are == 'presentations':
            start_frame = i + 1
            end_frame = start_frame

        # Even if the TIFF has data averaged across odor presentations, the YAML will
        # still always have one entry per presentation (so should have n_repeats
        # consecutive of each).
        elif tiff_frames_are == 'trial-averaged-odors':
            # TODO delete (was before adding no_seq_dupes)
            #start_frame = (i // n_repeats) + 1
            start_frame = i + 1
            end_frame = start_frame

        # str describing all odors presented on this trial
        odor_str = trial_data['odors']

        # Ideally would use a single master ledger of which odors should narrowly
        # activate a particular glomerulus, and check all odors for proximity to odors
        # in this list, but YAML not available here (at least not in jython stdlib),
        # so I couldn't use my tom_olfactometer_config YAML files directly.
        if 'glomerulus' in trial_data:
            odor_str += (' (%s)' % trial_data['glomerulus'])

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
            roi = TextRoi(text_x_pos, text_y_pos, odor_str)
            roi.setPosition(0, 0, t)

            if tiff_frames_are == 'time' and t == first_odor_frame:
                # TODO TODO TODO why is this not working? (this else branch *is* being
                # reached)
                roi.setColor(first_odor_frame_color)

            # TODO TODO TODO need to encode a global frame duration (of odor
            # presentation) somewhere, or maybe just have add a last_odor_frame, for
            # same reason it made sense to have this rather than a global frame offset
            # anyway...
            else:
                roi.setColor(default_color)

            roi.setFontSize(font_size)

            overlay.add(roi)

    imp.setOverlay(overlay)
    imp.show()


if __name__ == '__main__':
    overlay()

