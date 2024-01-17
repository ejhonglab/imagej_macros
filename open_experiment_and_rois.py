
#@ boolean (label="For motion correction eval only", value=false) mocorr_eval_only

from os.path import join, exists

from java.awt import Checkbox
from java.awt.event import ActionEvent

from ij import IJ
from ij.plugin.frame import RoiManager, SyncWindows
from ij.io import DirectoryChooser, Opener


# TODO if experiment / ROIs already open, maybe just save ROIs to ROI zip?
# changing cwd on load here might help? or can i get path of current tif?
def main():
    verbose = False

    if not mocorr_eval_only:
        load_rois = True

        # If a name is specified multiple times, that many copies of the TIFF will be
        # opened. Useful for having different types of overlays (currently haven't
        # figured out how to get them to co-exist...) side-by-side
        tiffs_to_load = [
            # TODO maybe still load raw.tif if mocorr.tiff not there?
            #'mocorr.tif',

            #'trial_dff.tif',
            #'trialmean_dff.tif',
            # TODO maybe load all files matching ../*/max_trialmean_dff.tif ?
            ##'max_trialmean_dff.tif',

            # TODO maybe also write and load an average TIFF? something like stddev too?

        # Intentionally duplicated, to have one w/ odor and one w/ ROI overaly
        # (as i can't currently support both, given how each is currently written)
        #] + 2 * [
        #    '../trial_dff_concat.tif',
        ] + 2 * [
            '../trialmean_dff_concat.tif',

        # TODO want this by default? show separately (via another hotkey? 3?)?
        # TODO also make a new hotkey to show trial_dff_concat.tif (+ a copy that shows
        # odors there)?
        ] + [
            # TODO find a way to not try syncing this w/ odor length ones, then
            # uncomment here are remove from '1' hotkey (branch below)
            #
            # all frames averaged (weighted equally). to compare ROIs to ~background
            # signal.
            #'../mocorr_concat_avg.tif',
        ]

    else:
        # TODO still overlay odor info in this case
        load_rois = False
        # TODO maybe also load raw in this case?
        tiffs_to_load = [
            # NOTE: i would include on the '2' hotkey (instead of this one), if i had a
            # way to automate not trying to sync this w/ the odor-length TIFFs
            #
            # all frames averaged (weighted equally). to compare ROIs to ~background
            # signal.
            '../mocorr_concat_avg.tif',

            # This should be a symlink to one ../suite2p/mocorr_concat.tif, which should
            # itself be a directory symlink to one of the suite2p run directories under
            # ../suite2p_runs (e.g. ../suite2p_runs/<run number>/suite2p)
            '../mocorr_concat.tif',
        ]

    if load_rois:
        # Will open ROI manager window if not already open.
        manager = RoiManager.getRoiManager()

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

    if verbose:
        print 'exp_dir:', exp_dir

    if load_rois:
        # TODO manager.reset() if path of new dir doesn't share the path up through the
        # <date>/<fly> parts (i.e. if it came from a diff fly)?

        roiset_path = join(exp_dir, 'RoiSet.zip')
        if verbose:
            print 'roiset_path:', roiset_path

        if not exists(roiset_path):
            print 'ROI zip', roiset_path, 'did not exist. not loading ROIs.'
        else:
            manager.runCommand('Open', roiset_path)

        # If any TIFF is specified multiple times in tiffs_to_load, and is in this list,
        # one will recieve this overlay and the other will receive the odor overlay.
        tiffs_to_start_with_roi_overlay = [
            'mocorr.tif',

            #'trial_dff.tif',
            #'trialmean_dff.tif',
            ##'max_trialmean_dff.tif',

            '../trial_dff_concat.tif',
            '../trialmean_dff_concat.tif',

            '../mocorr_concat_avg.tif',
        ]
        tiffs_to_start_with_odor_overlay = {
            x for x in set(tiffs_to_load) if tiffs_to_load.count(x) > 1
        }
    else:
        tiffs_to_start_with_roi_overlay = []
        tiffs_to_start_with_odor_overlay = set(tiffs_to_load)

    n_opened = 0
    for tiff_basename in tiffs_to_load:

        tiff_path = join(exp_dir, tiff_basename)
        if verbose:
            print 'tiff_path:', tiff_path

        if not exists(tiff_path):
            print 'tiff', tiff_path, 'did not exist!'
            continue

        opener = Opener()
        opener.open(tiff_path)

        #imp = IJ.getImage()
        # TODO maybe decide whether/how much to zoom based on some properties of this
        # ImageCanvas object?
        #canvas = imp.getCanvas()
        # no error but not intended effect
        #canvas.setMagnification(4.0)

        IJ.run("Set... ", "zoom=400")

        if tiff_basename in tiffs_to_start_with_odor_overlay:
            IJ.run('overlay odors')
            # So the second time we get this basename (and guaranteed we will),
            # it will get the ROI overlay.
            tiffs_to_start_with_odor_overlay.remove(tiff_basename)

        elif tiff_basename in tiffs_to_start_with_roi_overlay:
            IJ.run('overlay rois in curr z',
                'draw_labels=false draw_names=true black_behind_text=false'
            )

        n_opened += 1

    if n_opened > 1:
        # TODO delete zoom stuff above if i also get this to restore sizes (=zooms?)
        IJ.run('restore window positions')

        IJ.run('Synchronize Windows')

        window_syncer = SyncWindows.getInstance()
        assert window_syncer is not None

        # TODO may want to find Panel components member that is a Panel (and assert only
        # 1) rather than hardcoding index...
        #
        # This is a parent panel, but not the direct parent of the relevant checkboxes.
        parent_panel = window_syncer.components[0]

        # This should be the child Panel that contains the checkboxes.
        checkbox_panel = parent_panel.components[1]

        # TODO TODO possible to exclude mocorr_concat_avg.tif (currently last entry)
        # from this? it doesn't have an odor axis...
        # (or just don't load it under '2' hotkey, and give it a separate one...)

        for c in checkbox_panel.components:
            if c.label == 'Sync cursor':
                # Default for this is True
                c.setState(False)

            # TODO TODO how could i sync only specific ones?
            # manually would click in list. list component also available,
            # via parent_panel.components[0]
            # TODO could try just opening ones i don't want to sync after this
            elif c.label == 'Synchronize All':
                button = c
                # Should be the same as clicking the button.
                # https://stackoverflow.com/questions/4753004
                action_name = button.getActionCommand()
                event = ActionEvent(button, ActionEvent.ACTION_PERFORMED, action_name)
                for listener in button.getActionListeners():
                    listener.actionPerformed(event)

    IJ.setTool('polygon')


if __name__ == '__main__':
    main()

