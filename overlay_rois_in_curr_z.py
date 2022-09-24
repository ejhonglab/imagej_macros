
#@ boolean (label="Draw ROI names", value=false) draw_names
#@ boolean (label="Draw ROI labels", value=false) draw_labels
#@ boolean (label="Black behind text", value=false) black_behind_text

# Sadly, `from __future__ import print_function` does not work in this context

# Will remove any existing overlay

import time

from ij import IJ
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from ij.gui import RoiListener

from java.awt.event import KeyAdapter, KeyEvent


# TODO have overlay updated automatically if possible to trigger off of ROI changes
# (what i was attempting w/ ZRespectingRoiOverlayer below, and what i'm currently trying
# to do w/ OverlayUpdaterKeyListener)


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


# TODO TODO make also work if ROI selected in ROI manager list
# TODO TODO also make sure it works if ROI has just been drawn and added, but overlay
# not updated (also try to get it to work to also add the ROI, if it hasn't even been
# added to the ROI manager)
def update_matching_roi():
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

    rename_if_unchanged = True

    old_roi = manager.getRoi(index)
    assert manager.getRoiIndex(old_roi) == index
    if old_roi.equals(overlay_roi):
        if not rename_if_unchanged:
            if verbose:
                print 'ROI not changed! doing nothing!'
        else:
            # Second argument is default string. The empty string will *also* be
            # returned if user cancels the dialog.
            new_name = IJ.getString('New ROI name:', '')
            if new_name == '':
                return

            # TODO TODO rename anything sharing same name as well
            # (consistent w/ how number_rois.py works on numbered ROIs + QoL)

            manager.rename(index, new_name)

            # TODO also update overlay here, if i ever get that figured out

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


class OverlayUpdaterKeyListener(KeyAdapter):
    draw_names = False
    draw_labels = False
    black_behind_text = False

    def keyPressed(self, event):
        # TODO do i ignore the keyevent if imp isn't one we added listener too?
        # ig i shouldn't get events from any windows i didn't add a listener to
        # anyway...
        # TODO maybe share one listener for all images? would need something like a dict
        # to store settings then, w/ image ID as key...
        imp = event.getSource().getImage()
        key_code = event.getKeyCode()

        if key_code == KeyEvent.VK_T:
            # I might have encountered some times where the ROI manager add didn't
            # get processed before we try to update the overlay below... May need to
            # manually handle the add in here and deal with that hotkey if it keeps
            # happening.
            time.sleep(0.2)

        # TODO why does this one not seem to work, but t does?
        # (as in the original hotkey not getting triggered separately)
        elif key_code == KeyEvent.VK_R:
            # NOTE: I have a corresponding StartupMacros.fiji.ijm entry to disable the
            # default 'r' hotkey.
            # TODO implement a version of this but for deleting (or via arg?)
            update_matching_roi()

        elif key_code == KeyEvent.VK_DELETE:
            pass

        else:
            return

        # TODO TODO ideally, would still also update ROI overlay whenever an ROI stops
        # being edited (to revert a change that has not been saved into ROI manager w/
        # 'r', but that will stay changed in overlay until manually updated)
        # TODO could maybe do by also intercepting mouse clicks, though this listener
        # doesn't seem to do that

        # TODO ideally would also trigger when stuff is deleted / renamed / etc from ROI
        # manager window directly

        # TODO TODO may want my hotkey to clear the overlay to remove this listener
        # too... maybe just intercept that key in listener and have it delete itself?

        # TODO make sure these properties actually persist from when listener first
        # established
        overlay(imp,
            draw_names=self.draw_names,
            draw_labels=self.draw_labels,
            black_behind_text=self.black_behind_text
        )
        # TODO intercept at least t/r[/delete if i implement using that to delete ROIs]
        # TODO try to pass thru everything else somehow


# TODO probably just move this into the __init__ of the listener
def add_listener(imp, draw_names, draw_labels, black_behind_text):
    win = imp.getWindow()
    if win is None:
        # TODO might rather err here
        return

    canvas = win.getCanvas()
    kls = canvas.getKeyListeners()

    existing_listener = None
    for listener in kls:
        # type / isintance checks were not working
        if 'OverlayUpdaterKeyListener' in str(type(listener)):
            existing_listener = listener

    if existing_listener is not None:
        listener = existing_listener
    else:
        # TODO maybe pass image / image ID thru a custom __init__
        listener = OverlayUpdaterKeyListener()

    listener.draw_names = draw_names
    listener.draw_labels = draw_labels
    listener.black_behind_text = black_behind_text

    # TODO do i have to do this? if so, maybe wrap existing listeners and pass thru
    # everything but the few keys i want to use (t, r)?
    #map(canvas.removeKeyListener, kls)

    if existing_listener is None:
        canvas.addKeyListener(listener)


def overlay(imp=None, draw_names=False, draw_labels=False, black_behind_text=False):

    verbose = False

    if imp is None:
        imp = IJ.getImage()

    # didn't work. global dict seems to get cleaned up between runs.
    #image_id = imp.getID()
    #image_id2overlay_settings[image_id] = {
    #    'draw_names': draw_names,
    #    'draw_labels': draw_labels,
    #}

    if verbose:
        print 'n channels:', imp.getNChannels()
        print 'n slices:', imp.getNSlices()
        print 'n frames:', imp.getNFrames()

    volumetric = True

    # To allow this to work on a wider variety of TIFFs, not always so carefully
    # created, where there is just a single non-length-1 dimension (which actually
    # corresponds to Z, but the TIFF isn't constructed reflecting that).
    if imp.getNSlices() == 1:
        volumetric = False

        if imp.getNChannels() == 1 and imp.getNFrames() > 1:
            print('image is not properly volumetric. assuming T is Z.')
            set_roi_position_fn = lambda roi: roi.setPosition(roi.getZPosition())
        else:
            raise ValueError('image is not volumetric nor only a time dimension to '
                'assume is Z'
            )

    overlay = Overlay()

    manager = RoiManager.getInstance()
    if not manager:
        if verbose:
            print 'ROI manager not open. doing nothing.'

        return

    rois = manager.getRoisAsArray()

    if draw_names:
        draw_labels = True

    overlay.drawNames(draw_names)
    overlay.drawLabels(draw_labels)
    overlay.drawBackgrounds(black_behind_text)

    n_frames = imp.getNFrames()

    for roi in rois:
        roi = roi.clone()

        if volumetric:
            z = roi.getZPosition()

            if n_frames > 1:
                c = roi.getCPosition()

                # Don't need t because we are using 0 to have it overlay on all time
                # indices
                roi.setPosition(c, z, 0)
            else:
                roi.setPosition(z)
        else:
            set_roi_position_fn(roi)

        overlay.add(roi)

        if verbose:
            print 'roi:', roi
            print 'name:', roi.getName()
            group_num = roi.getGroup()
            print 'group:', group_num
            print 'group name:', roi.getGroupName(group_num)
            print ''

    imp.setOverlay(overlay)
    imp.show()


class ZRespectingRoiOverlayer(RoiListener):
    def roiModified(self, imp, mod_type):
        mod_type2name = {
            RoiListener.COMPLETED: 'COMPLETED',
            RoiListener.CREATED: 'CREATED',
            RoiListener.DELETED: 'DELETED',
            RoiListener.EXTENDED: 'EXTENDED',
            RoiListener.MODIFIED: 'MODIFIED',
            RoiListener.MOVED: 'MOVED',
        }
        print 'mod_type:', mod_type
        print 'mod type name:', mod_type2name[mod_type]
        overlay(imp)
        print ''


def main():
    #print 'listener containing only:', [x for x in dir(Roi) if 'listener' in x.lower()]
    # not sure why this isn't defined even though it's in the API docs...
    #print 'roi listeners:'
    #for listener in Roi.getListeners():
    #    print listener

    #overlayer = ZRespectingRoiOverlayer()
    #Roi.addRoiListener(overlayer)

    imp = IJ.getImage()
    if imp is None:
        return

    # TODO or can i just leave the original listener, and let it do the ROI
    # adding/updating/deleting? would i need to time.sleep then, to guarantee ROI change
    # made before updating overlay? or do they happen in a particular order anyway
    # (order in list?)?
    add_listener(imp, draw_names, draw_labels, black_behind_text)

    overlay(imp, draw_names=draw_names, draw_labels=draw_labels,
        black_behind_text=black_behind_text
    )


if __name__ == '__main__':
    main()
