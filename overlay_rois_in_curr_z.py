
#@ boolean (label="Draw ROI names", value=false) draw_names
#@ boolean (label="Draw ROI labels", value=false) draw_labels
#@ boolean (label="Black behind text", value=false) black_behind_text

# Sadly, `from __future__ import print_function` does not work in this context

# Will remove any existing overlay

from ij import IJ
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from ij.gui import RoiListener


def overlay(imp=None, draw_names=False, draw_labels=False, black_behind_text=False):

    if imp is None:
        imp = IJ.getImage()

    verbose = False

    overlay = Overlay()

    manager = RoiManager.getInstance()
    if not manager:
        if verbose:
            print 'ROI manager not open. doing nothing.'

        sys.exit()

    rois = manager.getRoisAsArray()

    if draw_names:
        draw_labels = True

    overlay.drawNames(draw_names)
    overlay.drawLabels(draw_labels)
    overlay.drawBackgrounds(black_behind_text)

    for roi in rois:
        roi = roi.clone()

        c = roi.getCPosition()
        z = roi.getZPosition()
        # Don't need t because we are using 0 to have it overlay on all time indices

        roi.setPosition(c, z, 0)
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

