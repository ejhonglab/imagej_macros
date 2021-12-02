
from os.path import join, exists

from ij import IJ
from ij.plugin.frame import RoiManager
from ij.io import DirectoryChooser, Opener
from ij.plugin import Zoom


# TODO if experiment / ROIs already open, maybe just save ROIs to ROI zip?
# changing cwd on load here might help? or can i get path of current tif?

def main():
    # Will open ROI manager window if not already open.
    manager = RoiManager.getRoiManager()

    load_rois = True

    rois = manager.getRoisAsArray()
    if len(rois) > 0:
        print ('ROI manager already has ROIs! assuming compatible.'
            ' will NOT load RoiSet.zip!'
        )
        load_rois = False

    chooser = DirectoryChooser('Select experiment directory...')

    # TODO maybe chooser.setDefaultDirectory to value of some environment variable, if
    # defined

    exp_dir = chooser.getDirectory()

    if not exp_dir:
        print 'no experiment directory selected'
        return

    print 'exp_dir:', exp_dir

    tiff_path = join(exp_dir, 'raw.tif')
    print 'tiff_path:', tiff_path

    if not exists(tiff_path):
        print 'tiff', tiff_path, 'did not exist! doing nothing.'
        return

    opener = Opener()
    opener.open(tiff_path)

    imp = IJ.getImage()

    # TODO maybe decide whether/how much to zoom based on some properties of this
    # ImageCanvas object?
    #canvas = imp.getCanvas()
    # no error but not intended effect
    #canvas.setMagnification(4.0)

    IJ.run("Set... ", "zoom=400")

    if load_rois:
        roiset_path = join(exp_dir, 'RoiSet.zip')
        print 'roiset_path:', roiset_path

        if not exists(roiset_path):
            print 'ROI zip', roiset_path, 'did not exist. not loading ROIs.'
            return

        manager.runCommand('Open', roiset_path)

    IJ.run('overlay rois in curr z',
        'draw_labels=false draw_names=true black_behind_text=false'
    )


if __name__ == '__main__':
    main()
