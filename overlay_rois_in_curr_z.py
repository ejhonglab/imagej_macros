
#@ boolean (label="Draw ROI names", value=false) draw_names
#@ boolean (label="Draw ROI labels", value=false) draw_labels
#@ boolean (label="Black behind text", value=false) black_behind_text

# Sadly, `from __future__ import print_function` does not work in this context

# Will remove any existing overlay

from ij import IJ
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from ij.gui import RoiListener


# TODO prevent selection / modification of overlay ROIs unless i can figure out how to
# propagate changes to them through to the ROI manager ROIs they correspond to in a
# transparent way

# TODO have overlay updated automatically if possible to trigger off of ROI changes
# (what i was attempting w/ ZRespectingRoiOverlayer below)

# TODO add hotkey to clear overlay? maybe add metadata to ROIs here to clear only the
# stuff we have drawn? probably not worth the effort and just hotkey to builtin overlay
# clear

def overlay(imp=None, draw_names=False, draw_labels=False, black_behind_text=False):

    verbose = False

    if imp is None:
        imp = IJ.getImage()

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
    #print 'listener containing only:', [y for x in dir(Roi) if 'listener' in x.lower()]
    # not sure why this isn't defined even though it's in the API docs...
    #print 'roi listeners:'
    #for listener in Roi.getListeners():
    #    print listener

    #overlayer = ZRespectingRoiOverlayer()
    #Roi.addRoiListener(overlayer)

    overlay(draw_names=draw_names, draw_labels=draw_labels,
        black_behind_text=black_behind_text
    )

