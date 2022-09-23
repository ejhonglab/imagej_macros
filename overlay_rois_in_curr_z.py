
#@ boolean (label="Draw ROI names", value=false) draw_names
#@ boolean (label="Draw ROI labels", value=false) draw_labels
#@ boolean (label="Black behind text", value=false) black_behind_text

# Sadly, `from __future__ import print_function` does not work in this context

# Will remove any existing overlay

from ij import IJ
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from ij.gui import RoiListener

from java.awt.event import KeyAdapter


# TODO have overlay updated automatically if possible to trigger off of ROI changes
# (what i was attempting w/ ZRespectingRoiOverlayer below, and what i'm currently trying
# to do w/ OverlayUpdaterKeyListener)

class OverlayUpdaterKeyListener(KeyAdapter):
    #image_id2overlay_settings = dict()
    draw_names = False
    draw_labels = False
    black_behind_text = False

    def keyPressed(self, event):
        imp = event.getSource().getImage()
        print str(self), 'id(self):', id(self)

        print 'draw_names:', self.draw_names, 'draw_labels:', self.draw_labels, \
            'black_behind_text:', self.black_behind_text

        print 'imp:', str(imp), 'image_id:', imp.getID()
        print 'key:', str(event.getKeyCode())
        print ''

        # TODO intercept at least t/r[/delete if i implement using that to delete ROIs]
        # TODO try to pass thru everything else somehow


def add_listener(imp, draw_names, draw_labels, black_behind_text):
    win = imp.getWindow()
    if win is None:
        # TODO might rather err here
        return

    canvas = win.getCanvas()
    kls = canvas.getKeyListeners()

    existing_listener = None
    print 'listeners:'
    for listener in kls:
        print listener
        # type / isintance checks were not working
        if 'OverlayUpdaterKeyListener' in str(type(listener)):
            print 'found existing listener!'
            existing_listener = listener
    print ''

    if existing_listener is not None:
        print 'using existing listener!'
        listener = existing_listener
    else:
        # TODO maybe pass image / image ID thru a custom __init__
        listener = OverlayUpdaterKeyListener()

    listener.draw_names = draw_names
    listener.draw_labels = draw_labels
    listener.black_behind_text = black_behind_text

    # TODO TODO do i have to do this? if so, maybe wrap existing listeners and pass
    # thru everything but the few keys i want to use (t, r)?
    #map(canvas.removeKeyListener, kls)

    if existing_listener is None:
        canvas.addKeyListener(listener)


def overlay(imp=None, draw_names=False, draw_labels=False, black_behind_text=False):

    verbose = False

    if imp is None:
        imp = IJ.getImage()

    add_listener(imp, draw_names, draw_labels, black_behind_text)

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


if __name__ == '__main__':
    #print 'listener containing only:', [x for x in dir(Roi) if 'listener' in x.lower()]
    # not sure why this isn't defined even though it's in the API docs...
    #print 'roi listeners:'
    #for listener in Roi.getListeners():
    #    print listener

    #overlayer = ZRespectingRoiOverlayer()
    #Roi.addRoiListener(overlayer)

    overlay(draw_names=draw_names, draw_labels=draw_labels,
        black_behind_text=black_behind_text
    )

