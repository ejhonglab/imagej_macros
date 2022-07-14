
from ij import IJ
from ij.gui import Roi
from ij.plugin.frame import RoiManager


# TODO also try to just have this work automatically via RoiListener / similar?
# why wasn't that working in overlay_rois_in_curr_z.py again?

verbose = False

def print_roi(roi):
    print 'roi:', roi

    if roi is None:
        print ''
        return

    print 'name:', roi.getName()

    print 'C:', roi.getCPosition()
    print 'Z:', roi.getZPosition()
    print 'T:', roi.getTPosition()

    #print 'bounds:', roi.getBounds()

    # TODO this include offset?
    #print 'polygon:', roi.getPolygon()

    print 'is active overlay?', roi.isActiveOverlayRoi()

    # not sure what this int means, but maybe it can indicate whether we are editing it
    # still?
    print 'state:', roi.getState()

    #print 'properties:', roi.getProperties()
    #print 'debug info:', roi.getDebugInfo()

    print ''


# TODO TODO test whether roi.equals works for main subclasses i wanna use
# (docs just refer to rectangles, but i think other roi subclasses might override)
# (could try using roi.clone + changing some things to test?)

def rois_equal(roi1, roi2):
    # All of these should be names of (callable) methods associated with ROI objects.
    # https://imagej.nih.gov/ij/developer/api/ij/ij/gui/Roi.html
    attrs_to_compare = [
        'getName',

        # TODO TODO check we do get collisions if we have one Z with two ROIs, one drawn
        # on a movie with a time dimension, and one drawn on a projection that doesn't.
        # see overlay_rois_in_curr_z.py:set_roi_position_fn for related consideration.

        #'getCPosition',
        'getZPosition',
        #'getTPosition',

        # Only checking (name, C, Z, T), as:
        # 1) We should have edited the corresponding overlay ROI points at this point
        #    anyway.
        # 2) We should only ever have one ROI with all of these the same (should rename
        #    otherwise)
        #'getBounds',
        # This one wouldn't work anyway, neither via == nor .equals
        # getFloatPolygon might, or might need to implement my own polygon comparison
        #'getPolygon',
    ]
    def get_attr(roi, attr):
        attr_getter = getattr(roi, attr)
        return attr_getter()

    for attr in attrs_to_compare:
        roi1_attr = get_attr(roi1, attr)
        roi2_attr = get_attr(roi2, attr)

        if verbose:
            print 'attr:', attr, 'roi1:', roi1_attr, 'roi2:', roi2_attr

        # TODO delete eventually if not needed
        #if attr in ('getBounds', 'getPolygon'):
        #    eq1 = roi1_attr.equals(roi2_attr)
        #    eq2 = (roi1_attr == roi2_attr)
        #    assert eq1 == eq2
        #

        if roi1_attr != roi2_attr:
            if verbose:
                print 'attrs not equal! breaking!'

            return False

    return True


def main():
    manager = RoiManager.getInstance()
    if not manager:
        if verbose:
            print 'ROI manager not open. doing nothing.'
        return

    imp = IJ.getImage()
    overlay_roi = imp.roi

    if overlay_roi is None:
        if verbose:
            print 'no active ROI on current image!'
        return

    if not overlay_roi.isActiveOverlayRoi():
        # (may not be reachable. could test by selecting directly from ROI manager?)
        if verbose:
            print 'ROI active on current image is not an overlay ROI!'
        return

    # TODO delete
    if verbose:
        print ''
        print 'overlay roi:'
        print_roi(overlay_roi)
    #

    state_int = overlay_roi.getState()

    states = [
        # From ImageJ source code.
        'CONSTRUCTING',
        'MOVING',
        'RESIZING',
        'NORMAL',
        'MOVING_HANDLE',
    ]
    state = None
    for state_name in states:
        if state_int == getattr(Roi, state_name):
            state = state_name
    assert state is not None

    # TODO may need to fail / warn / popup / finalize (via abortModification?)
    # if state isn't NORMAL (seems ok to just not support this for now actually.
    # state was NORMAL in testing as I'd actually use this.)
    assert state == 'NORMAL', 'state of overlay ROI indicated it was being modified'

    # TODO TODO maybe my overlay creation should be making some maybe i should cache a
    # list of ROIs in overlay creation (maybe via a listener for [each?] overlay roi?)
    # -> previous ROIs, and then just get the index of the currently selected one?
    # (not sure how to even have global state, or if it's possible here tho...)
    # TODO or maybe i should just use listeners to keep a list of overlay rois and roi
    # manager rois in sync if i'm gonna go that route anyway...
    # NOTE: Roi.[get/set]PreviousRoi are not what I want, as there is only one global
    # Roi stored there.

    rois = manager.getRoisAsArray()
    index = None
    n_matching = 0
    for i, roi in enumerate(rois):
        if rois_equal(overlay_roi, roi):
            index = i
            n_matching += 1

    assert index is not None, 'no matching ROI found!'
    # TODO TODO test meaningful error message if there are two w/ same name in same
    # z slice coordinate
    assert not (n_matching > 1), 'multiple ROIs with same name in >=1 Z index'

    old_roi = manager.getRoi(index)
    assert manager.getRoiIndex(old_roi) == index
    if old_roi.equals(overlay_roi):
        if verbose:
            print 'ROI not changed! doing nothing!'
        return

    # TODO delete
    if verbose:
        print('matching ROI:')
        print_roi(old_roi)
    #

    manager.setRoi(overlay_roi, index)

    '''
    # TODO might need manager.deselect() first if selection method i use doesn't clear
    # existing selection first

    manager.select(index)

    # TODO delete
    assert manager.isSelected(index)
    selected_roi_indices = manager.getSelectedIndexes()
    assert len(selected_roi_indices) == 1
    assert selected_roi_indices[0] == index
    #

    manager.runCommand("Update")
    '''

    # TODO make sure (C, Z, T) are all preserved in update process
    # (or at least Z... see related note in rois_equal)
    new_roi = manager.getRoi(index)
    assert rois_equal(new_roi, overlay_roi)
    assert new_roi.equals(overlay_roi)
    assert rois_equal(old_roi, new_roi)

    # TODO TODO if i can find a way to share global state across plugins, want to check
    # which type of overlay is active and re-update it w/ same parameters, after
    # updating (so that future checks compare overlay and ROI manager ROIS are correct)
    # TODO or could just check each of the flags indicating whether labels / names / etc
    # should be drawn by inspection of current image / overlay?


if __name__ == '__main__':
    main()

