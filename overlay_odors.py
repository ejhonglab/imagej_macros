
# Will remove any existing overlay

import json
from os.path import split, join, exists

from ij import IJ
from ij.gui import Overlay, TextRoi


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

    if verbose:
        from pprint import pprint
        pprint(trial_data_list)
        print ''

    overlay = Overlay()

    for trial_data in trial_data_list:
        start_frame = trial_data['start_frame'] + 1
        first_odor_frame = trial_data['first_odor_frame'] + 1
        end_frame = trial_data['end_frame'] + 1

        # str describing all odors presented on this trial
        odors = trial_data['odors']

        # TODO TODO do something with first_odor_frame (change color during odor pulse?
        # would need info about end...) (could at least do on first frame...)
        for t in range(start_frame, end_frame + 1):
            # TODO find another version of constructor that gets font smaller / nicer
            # https://imagej.nih.gov/ij/developer/api/ij/ij/gui/TextRoi.html
            #roi = TextRoi(10, 12, 40, 10, odors)
            roi = TextRoi(10, 12, odors)
            roi.setPosition(0, 0, t)
            overlay.add(roi)

    imp.setOverlay(overlay)
    imp.show()


if __name__ == '__main__':
    overlay()

