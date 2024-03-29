
#@ boolean (label="Draw ROI names", value=false) draw_names
#@ boolean (label="Draw ROI labels", value=false) draw_labels
#@ boolean (label="Black behind text", value=false) black_behind_text

# Sadly, `from __future__ import print_function` does not work in this context

# Will remove any existing overlay

from os import getenv
from os.path import expanduser, split, join, isdir, exists
import time
import shlex
from pprint import pprint

from java.lang import ProcessBuilder
from java.io import File
from java.awt.event import KeyAdapter, KeyEvent
from java.util import Timer, TimerTask
from java.net import ServerSocket, SocketTimeoutException, BindException
from java.io import DataInputStream
from ij import IJ
from ij.gui import Overlay, Roi
from ij.plugin.frame import RoiManager
from ij.gui import RoiListener


# TODO have overlay updated automatically if possible to trigger off of ROI changes
# (what i was attempting w/ ZRespectingRoiOverlayer below, and what i'm currently trying
# to do w/ OverlayUpdaterKeyListener)

# TODO one version of this (w/ modifier in addition to F2 hotkey?) to open 2 copied of
# either ../trial_dff_concat.tif or trialmean_dff_concat.tif, so i can sync "time"points
# again, and have one for odor overlay and one for time

verbose = False
_debug = False

# TODO TODO TODO either here or via startup macros, override / add-to default 't'
# actions to also prompt for a name for the roi (at least shift+t or something)?
# TODO TODO TODO try to get to update in all windows with overlays when any window with
# an overlay has an ROI change (change so i only have one listener and register it w/
# all the windows?)
# TODO TODO make n -> renumber_rois also update any active overlays
# (currently just need to press n 2(-3?) times and it will)
class OverlayUpdaterKeyListener(KeyAdapter):
    draw_names = False
    draw_labels = False
    black_behind_text = False

    # TODO straightforward to make an __init__? need to call super()?
    # (would want to init ServerSocket there, if that approach works at all)

    def keyPressed(self, event):
        # TODO do i ignore the keyevent if imp isn't one we added listener too?
        # ig i shouldn't get events from any windows i didn't add a listener to
        # anyway...
        # TODO maybe share one listener for all images? would need something like a dict
        # to store settings then, w/ image ID as key...
        imp = event.getSource().getImage()
        key_code = event.getKeyCode()

        # This is the default ROI manager hotkey for adding an ROI.
        # TODO can we override it? comment if we can't / don't want to
        if key_code == KeyEvent.VK_T:
            # I might have encountered some times where the ROI manager add didn't
            # get processed before we try to update the overlay below... May need to
            # manually handle the add in here and deal with that hotkey if it keeps
            # happening.
            time.sleep(0.2)

            # TODO TODO TODO when current odor is a diagnostic w/ a glomerulus
            # specified, default to the name of that glomerulus for new_name
            # (don't do if we already have that ROI in the plane tho)
            # TODO or maybe have a modifier key / another hotkey use that name, and
            # otherwise just keep current behavior (or auto pick next number otherwise)?
            #
            # (w/o being able to share code, would require copying a lot from
            # overlay_odors.py. might wanna merge that into this anyway...)

        # TODO why does this one not seem to work, but t does?
        # (as in the original hotkey not getting triggered separately)
        elif key_code == KeyEvent.VK_R:
            # NOTE: I have a corresponding StartupMacros.fiji.ijm entry to disable the
            # default 'r' hotkey.
            # TODO implement a version of this but for deleting (or via arg?)
            update_matching_roi()

        # NOTE: both backspace and delete seem to delete overlay ROIs by default
        # (but not from the manager, just from the overlay). so I will make a hotkey to
        # make it do nothing in my startup config.
        # actually i can't get a do-nothing macro w/ "[backspace]" to work...
        # so i'll override default d->draw instead
        #elif key_code == KeyEvent.VK_BACK_SPACE:
        elif key_code == KeyEvent.VK_D:
            delete_matching_roi()

        # 'g' doesn't seem to be a default hotkey ('G' is screenshot)
        elif key_code == KeyEvent.VK_G:
            remove_uncertainty_suffix()

        # TODO test if this works (doesn't seem to, i.e. the overlay is not updated
        # after rois are renumbered). might just need to refactor and explicitly call
        # renumber in here (at least i can still double tap n to update, as it is now)
        elif key_code == KeyEvent.VK_N:
            pass

        # shift+h not mentioned in docs I can see, but it does seem to do something
        # Don't think I care about it though, so I'm unmapping it via startup config.
        #
        # TODO why the event.isShiftDown()? what is 'h' by default?
        elif key_code == KeyEvent.VK_H and event.isShiftDown():
            plot_roi_responses(hallem=True)
            return

        elif key_code == KeyEvent.VK_P:
            # Ctrl/Shift + p already have builtin ImageJ meanings
            # (I could probably override them to do nothing, but still...)
            plot_roi_responses(add_to_existing_plot=event.isAltDown())
            return

        #elif key_code == KeyEvent.VK_0:
        #    # TODO get max odor response (via script similar to plot_roi_responses,
        #    # or by a new arg to plot_roi_responses) -> go to index of that odor
        #    #plot_roi_responses(add_to_existing_plot=event.isAltDown())
        #    return

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


def rename_roi(manager, roi, new_name=None, default_new_name=None,
    check_name_unique_in_plane=True):
    """Renames ROI, prompting user for name if `new_name=None`.

    Args:
        default_new_name: if user will be prompted for ROI name, this will be what that
            text entry box starts with. if not passed, will use existing ROI name.
            unused if `new_name` is passed.

    Raises assertion error if `check_name_unique_in_plane=True`, so that future
    matching on (name, plane) isn't broken.
    """
    old_name = roi.getName()

    if new_name is None:
        if default_new_name is None:
            default_new_name = old_name

        # Second argument is default string. The empty string will *also* be
        # returned if user cancels the dialog.
        new_name = IJ.getString('New ROI name:', default_new_name)

        if len(new_name) == 0:
            return

    else:
        # TODO other checks?
        assert len(new_name) > 0

    if new_name == old_name:
        return

    # TODO test!
    #
    # checking no other ROIs in same plane have same new_name (as then future
    # attempts to find matching ROI will err, and i have to change manually from
    # ROI manager)
    if check_name_unique_in_plane:
        curr_z = roi.getZPosition()
        rois = manager.getRoisAsArray()
        n_matching = 0
        for i, curr_roi in enumerate(rois):
            if curr_roi.getZPosition() != curr_z:
                continue

            if curr_roi.getName() == new_name:
                n_matching += 1

        assert n_matching == 0, ('%d ROI(s) with name="%s" already in z=%d' %
            (n_matching, new_name, curr_z)
        )

    # TODO TODO rename anything sharing same name as well
    # (i.e. in other planes)
    # (consistent w/ how number_rois.py works on numbered ROIs + QoL)

    index = manager.getRoiIndex(roi)
    manager.rename(index, new_name)


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


def check_roi_state(roi, expected_state='NORMAL'):
    state_int = roi.getState()
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
    # NOTE: this does randomly get triggered sometimes (not sure what state(s) it tends
    # to be in though. didn't have RHS of assertion to print at the time.
    assert state == expected_state, (
        'state (%s) != expected_state (%s)' % (state, expected_state)
    )


def get_overlay_roi(check_state=True):
    # TODO doc type of return
    """Returns selected ROI in overlay
    """
    # TODO might want to check if this is None...
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

    if check_state:
        # TODO may need to fail / warn / popup / finalize (via abortModification?)
        # if state isn't NORMAL (seems ok to just not support this for now actually.
        # state was NORMAL in testing as I'd actually use this.)
        check_roi_state(overlay_roi)

    return overlay_roi


def find_roi_manager_index(target_roi, manager=None):
    """Returns (manager, index).

    Returned index is None if no matching ROI.
    Returned manager is None if ROI manager not open (and not passed in).
    """
    if manager is None:
        manager = RoiManager.getInstance()
        if not manager:
            if verbose:
                print 'ROI manager not open!'

            return None, None

    rois = manager.getRoisAsArray()
    index = None
    n_matching = 0
    for i, roi in enumerate(rois):
        if rois_equal(target_roi, roi):
            index = i
            n_matching += 1

    if index is None:
        if verbose:
            print 'no matching ROI!'

        return manager, None

    # TODO TODO test meaningful error message if there are two w/ same name in same
    # z slice coordinate
    assert not (n_matching > 1), 'multiple ROIs with same name in >=1 Z index'

    return manager, index


def find_overlay_roi_manager_index(manager=None, **kwargs):
    """Returns (overlay_roi, ROI_manager, index).

    If no overlay ROI is selected, None is returned for `overlay_roi`, `manager`, and
    `index`. Returned `manager` is None if ROI manager not open (and not passed in).

    Args:
        manager: ROI manager instance (will try to get open one if not passed)
        **kwargs: passed to `get_overlay_roi`
    """
    overlay_roi = get_overlay_roi(**kwargs)
    if overlay_roi is None:
        # TODO TODO TODO check whether any code currently needs manager if other stuff
        # would be None. would complicate implementation if i needed that.
        # (couldn't do this. would still need to get manager.)
        # TODO or maybe allow None/similar sentinel input to find_roi_manager to just
        # return the manager without finding index?
        return None, None, None

    # TODO maybe my overlay creation should be making some list of ROIs in overlay
    # creation (maybe via a listener for [each?] overlay roi?) -> previous ROIs, and
    # then just get the index of the currently selected one?
    # (would then not have to rely on matching name i guess?)
    # (not sure how to even have global state, or if it's possible here tho...)
    # TODO or maybe i should just use listeners to keep a list of overlay rois and roi
    # manager rois in sync if i'm gonna go that route anyway...
    # NOTE: Roi.[get/set]PreviousRoi are not what I want, as there is only one global
    # Roi stored there.

    manager, index = find_roi_manager_index(overlay_roi)
    return overlay_roi, manager, index


# TODO also one for adding/toggling some of these suffixes?
def remove_uncertainty_suffix():
    overlay_roi, manager, index = find_overlay_roi_manager_index()
    if overlay_roi is None or manager is None or index is None:
        return

    roi = manager.getRoi(index)
    old_name = roi.getName()
    # this will remove any amount/ordering of '+' and '?' characters from right end of
    # name
    new_name = old_name.rstrip('+?')
    rename_roi(manager, roi, new_name)


# TODO make also work if ROI selected in ROI manager list
# TODO TODO also make sure it works if ROI has just been drawn and added, but overlay
# not updated (also try to get it to work to also add the ROI, if it hasn't even been
# added to the ROI manager)
def update_matching_roi():
    overlay_roi, manager, index = find_overlay_roi_manager_index()
    if overlay_roi is None or manager is None or index is None:
        return

    old_roi = manager.getRoi(index)
    assert manager.getRoiIndex(old_roi) == index

    rename_if_unchanged = True

    # TODO some reason i'm not using rois_equal here? i think it's intentional...
    if old_roi.equals(overlay_roi):
        # TODO TODO factor out this roi renaming (-> use to modify suffixes in hotkeys
        # too)
        if not rename_if_unchanged:
            if verbose:
                print 'ROI not changed! doing nothing!'
        else:
            # without the second parameter passed, rename_roi will prompt for new name
            # (with text in entry box starting at old name)
            rename_roi(manager, old_roi)

        return

    manager.setRoi(overlay_roi, index)

    # TODO make sure (C, Z, T) are all preserved in update process
    # (or at least Z... see related note in rois_equal) (still relevant?)
    new_roi = manager.getRoi(index)
    assert rois_equal(new_roi, overlay_roi)
    assert new_roi.equals(overlay_roi)
    assert rois_equal(old_roi, new_roi)


def delete_matching_roi():
    overlay_roi, manager, index = find_overlay_roi_manager_index()
    if overlay_roi is None or manager is None or index is None:
        return

    # Just in case the .select call adds to selection rather than overwriting it.
    # Not sure of the behavior.
    manager.deselect()

    if verbose:
        print 'deleting roi at index', str(index)

    # TODO try to not switch indices of slice of movie we are viewing
    # or save -> restore, via something like:
    #imp = IJ.getImage()
    #imp.setT(odor_index + 1)
    # (may need to do w/ other dimensions? just T may also be what i need)

    manager.select(index)
    manager.runCommand('Delete')

    # TODO deselect overlay automatically if possible (to achieve same thing as clicking
    # off of it, where it goes away)


# TODO move this to its own script, if i figure out how to factor the stuff this shares
# w/ update_matching_roi out into a package or something
# (though if IJ.run just won't ever work inside the listener, not sure i can factor it
# out anyway... not sure why it froze when i was trying to call update_matching_roi that
# way)
def plot_roi_responses(source_bashrc=True, add_to_existing_plot=False, hallem=False,
    compare_to_cached=False):

    # NOTE: not using find_overlay_roi_manager_index, as that currently returns None
    # manager if no matching overlay_roi. we still want manager in here.

    # seems this will be None if i just finished drawing an ROI (as currently
    # implemented at least) (or presumably also if i'm drawing an ROI)
    overlay_roi = get_overlay_roi()

    manager = RoiManager.getInstance()
    if manager is None:
        return

    added_temp_roi = False

    # TODO delete
    verbose = False
    #
    if overlay_roi is not None:
        # TODO change to work w/ multiple ROIs selected? ig it would need to be from the
        # list though (is it possible to select multiple overlay ROIs?)?
        _, index = find_roi_manager_index(overlay_roi, manager=manager)
        if index is None:
            return

        # TODO if i actually need the deselect() call further down, just move outside
        # conditional and have one call
        manager.deselect()
    else:
        prev_rois = manager.getRoisAsArray()

        #TODO delete
        if verbose:
            print 'adding roi'
        #

        # TODO TODO TODO detect if roi is finished before adding
        # why do we not get the "Selection is not complete" popup we would get if we
        # used the builtin 't' command to add currently-being-drawn-or-done ROI to
        # manager? do i need to pass the image in as well or something?

        # TODO may want to take steps to ensure we aren't re-adding selected ROIs
        # already in manager (or anything like that)

        # TODO detect if image has "an active selection" (that is a finished ROI, in
        # case possible for it to not be...) -> don't bother running 'Add' cmd if not

        manager.runCommand('Add')
        # see also 2 add(...) call options (both have more args...)
        # TODO need to deselect after or nah?
        #manager.addRoi(overlay_roi)

        if len(prev_rois) + 1 != len(manager.getRoisAsArray()):
            return

        temp_roi_index = len(prev_rois)
        index = temp_roi_index

        added_temp_roi = True

    # TODO may need to handle case where there is only one ROI, cause not sure i want to
    # support loading .roi files (instead of the RoiSet.zip files)
    # TODO proper java way to get temp file paths?
    # TODO or maybe save as a hidden file in the image directory?
    tmp_roiset_zip_path = '/tmp/imagej_macros.plot_roi_responses.RoiSet.zip'
    success = manager.save(tmp_roiset_zip_path)
    assert success, 'saving ROIs to %s failed!' % tmp_roiset_zip_path

    if added_temp_roi:
        # Just in case the .select call adds to selection rather than overwriting it.
        # Not sure of the behavior.
        manager.deselect()

        manager.select(temp_roi_index)
        manager.runCommand('Delete')

        assert len(prev_rois) == len(manager.getRoisAsArray())

    # TODO assert this exists?
    plot_script_path = expanduser(getenv(
        'HONG_IMAGEJ_PLOT_SCRIPT', '~/src/al_analysis/plot_roi.py'
    ))
    plot_script_dir = split(plot_script_path)[0]

    imp = IJ.getImage()
    file_info = imp.getOriginalFileInfo()
    analysis_dir = file_info.directory

    # shlex.quote not available in this jython stdlib, but want to at least try to
    # escape spaces
    analysis_dir = "'%s'" % analysis_dir

    # TODO TODO env var(s) to select which conda env / venv to use
    # (default to trying conda env w/ name "al_analysis")
    # TODO TODO or default to .venv/venv in plot_script_path?
    # TODO TODO support using a venv? how?

    # Seems to work (at least if started from a terminal...)
    conda_env_name = getenv(
        'HONG_IMAGEJ_PLOT_SCRIPT_CONDA_ENV',
        # TODO delete usage of AL_ANALYSIS_CONDA_ENV (would just need to get sam to
        # update his config) (to be consistent w/ name of env var above, and more
        # agnostic to which plotting script we use)
        getenv('AL_ANALYSIS_CONDA_ENV')
    )

    venv_python = None
    if conda_env_name is None:
        # TODO also env var to force a path here?
        possible_venv_dir_names = ['venv', '.venv']

        for n in possible_venv_dir_names:
            venv_dir = join(plot_script_dir, n)
            if not isdir(venv_dir):
                continue

            if verbose:
                print('using venv found at: ' + venv_dir)

            # Assuming python -> python3 (seems to be reliable)
            venv_python = join(venv_dir, 'bin', 'python')
            assert exists(venv_python), 'venv dir existed by python executable did not'

            break

        if venv_python is None:
            conda_env_name = 'al_analysis'
            if verbose:
                print('did not find venv in ' + plot_script_dir)
                print('defaulting to conda env name: ' + conda_env_name)

    if conda_env_name is not None:
        #conda_path = expanduser('~/anaconda3/condabin/conda')
        # Now that I'm sourcing ~/.bashrc, this should be fine, and it doesn't matter if
        # the conda executable is in the same path then (e.g. miniconda)
        conda_path = 'conda'

        # NOTE: --no-capture-output became available sometime between conda
        # 4.7.11 and 4.12.0
        # TODO either try w/ --no-capture-output first, falling back to not using it
        # (which error to catch? easy?) or check conda version first. or enforce
        # >=4.12.0 (or whichever earlier version actually introduced this flag)
        env_cmd_prefix = ('{conda_path} run -n {conda_env_name} --no-capture-output'
            ).format(conda_path=conda_path, conda_env_name=conda_env_name)
    else:
        assert venv_python is not None
        # TODO test!
        env_cmd_prefix = venv_python

    cmd = ('{env_cmd_prefix} {plot_script_path} -d {analysis_dir} '
        '-r {tmp_roiset_zip_path} -i {index}').format(
        env_cmd_prefix=env_cmd_prefix, plot_script_path=plot_script_path,
        analysis_dir=analysis_dir, tmp_roiset_zip_path=tmp_roiset_zip_path, index=index
    )

    if add_to_existing_plot:
        # -a/--add
        cmd = cmd + ' -a'

    if hallem:
        # -H/--hallem
        cmd = cmd + ' -H'

    if not compare_to_cached:
        # -n/--no-compare
        cmd = cmd + ' -n'

    profile = False
    # NOTE: requires line_profiler installed in plot script environment
    # (via `pip install line-profiler`)
    # currently need to `pkill -SIGINT -f '/plot_roi'` to kill script and end timing
    #
    # should save profiling results to <plot-script>.lprof (in same directory as plot
    # script path, probably). can view results via `python -m line_profiler <.lprof>`
    # (it'll tell you how to view results too. you can pass `-u 1` option (for units to
    # be in seconds) after the fact too.)
    if profile:
        cmd = 'LINE_PROFILE=1 {cmd}'.format(cmd=cmd)

    # TODO technically could probably avoid sourcing + even activating conda environment
    # as long as we already have one plotting server process running (cause the
    # non-stdlib imports don't happen in the client path in al_analysis/plot_roi.py)

    # TODO why does this not seem to produce a pstree output that has an additional bash
    # process between ImageJ-linux64 and the first python descendent (presumably the
    # server plot_roi.py process)
    if source_bashrc:
        # -i flag to initial bash call caused bug where on subsequent calls, ImageJ
        # process would stop (presumably because some child process was waiting for
        # input when it would never get any?). something like this:
        # https://unix.stackexchange.com/questions/294471
        #
        # TODO actually test i can still get this to set environment variables as i
        # needed, if i wanted to use imagej started from default (/ simply generated)
        # .desktop file, which doesn't set any env vars (if not, may as well delete all
        # source_bashrc code... esp if i can't fix why previous line caused [most of?]
        # process-being-stopped bug)
        cmd = 'bash -c "source ~/.bashrc && {cmd}"'.format(cmd=cmd)

    # TODO delete
    verbose = True
    #
    if verbose:
        print 'running:', cmd

    cmd_list = shlex.split(cmd)

    # TODO tried: https://stackoverflow.com/questions/3936023 to redirect stdout/err to
    # imagej console, but while i can see the python traceback if ij is started from
    # terminal (in terminal is the only place i can see it), i can't see it in console.
    # TODO do i need to get something from proc? just not possible (this way?) for some
    # reason?
    pb = ProcessBuilder(cmd_list)

    pb.directory(File(plot_script_dir))

    # TODO or maybe i actually want to capture the output, and print it?
    # could not see python process output (in terminal, at least, and probably also in
    # ImageJ console) without these (or pb.inheritIO(), presumably)
    #pb.redirectOutput(Redirect.INHERIT)
    #pb.redirectError(Redirect.INHERIT)
    # TODO maybe see what pb.redirectInput() is by default?
    # TODO check that this also handles stderr, and isn't introducing additional errors
    # by maybe redirecting stdin (if that could even be an issue?) unlike above
    # (before deleting above, previous way of doing it)
    pb.inheritIO()

    # TODO print out PID started? other details?

    proc = pb.start()

    # TODO TODO how to get something from the script? ideally w/o using files behind the
    # scenes... (want to be able to jump to max response index, or cycle through them in
    # order) (see what i'm doing w/ check_for_odor_index. solved problem.)

    # TODO possible to print when things proc ends (for debugging)?


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

    # TODO comment explaining how drawNames is different from drawLabels...
    # NOTE: draw_names=true seems to be only one set by my hotkeys.
    # draw_labels is always false there.
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


# https://docs.oracle.com/javase/tutorial/networking/sockets/clientServer.html
# just an arbitrary port
# TODO log which port we are listening on?
port = 49007
timeout_ms = 100
server = None

# https://stackoverflow.com/questions/5680259
#
# TODO why is it not an issue that this overlay script gets invoked multiple times?
# what is guaranteeing this is not conflicting with past runs (it seems to not though)?
# TODO try to move this to an init method, if it works, to re-use server.
# matter? seems ok here...
try:
    server = ServerSocket(port)

    # TODO TODO TODO set recieve buffer to just be able to store one int (would it keep
    # getting overwritten with most recent? that's what i'd want)?
    # (to worry less about stale stuff. may still want to deal with it...)
    server.setSoTimeout(timeout_ms)

except BindException:
    print 'another server already bound on port %d!' % port


def check_for_odor_index(imp):
    if server is None:
        if _debug:
            print 'server was never set up (port was already bound)!'
            print ''

        return

    if _debug:
        print 'calling server.accept() to make client'
        print ''

    try:
        # TODO TODO can i have multiple server.accept() calls (as-is)?
        client = server.accept()
    except SocketTimeoutException:
        if _debug:
            print 'accept timed out!'

        return

    client_stream = client.getInputStream()
    data_stream = DataInputStream(client_stream)

    if _debug:
        print 'trying to read integer'

    # TODO ints in same format as if we write them in the simplest way from
    # python (try stuff ~5-20k)? maybe try readLong?
    odor_index = data_stream.readInt()

    if _debug:
        print 'odor_index received:', odor_index

    # TODO TODO broaden support for TIFFs w/ # timepoints = total number of
    # presentations OR full number of timepoints (= # frames). see what odor overlay is
    # doing.

    # SyncWindows should handle propagating to other windows (if any).
    # My opening macro should open SyncWindows with the appropriate settings.
    imp.setT(odor_index + 1)

    client.close()
    data_stream.close()


class CheckOdorIndex(TimerTask):
    def __init__(self, imp):
        self.imp = imp
        # TODO work? needed?
        super(CheckOdorIndex, self).__init__()

    def run(self):
        check_for_odor_index(self.imp)


# TODO probably just move this into the __init__ of the listener
def add_listeners(imp, draw_names, draw_labels, black_behind_text):
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

        # current implementation will only let this work on the first image an ROI
        # overlay is attached to (port will be taken in all future cases)

        # TODO need to try to associate this with some other object that is likely to
        # persist?
        # NOTE: currently relying on this being created only when first listener is, in
        # order to not have duplicates. if this checking was handled separately, we
        # could use one without the other, but maybe we don't need to.
        timer_task = CheckOdorIndex(imp)
        # TODO could also try Timer(True) to specify it should run as a daemon
        timer = Timer()
        # TODO log id(...) of timer to try to debug where stuff is freezing?
        # Should be in milliseconds
        timer.scheduleAtFixedRate(timer_task, 0, 2 * timeout_ms)


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
    add_listeners(imp, draw_names, draw_labels, black_behind_text)

    overlay(imp, draw_names=draw_names, draw_labels=draw_labels,
        black_behind_text=black_behind_text
    )


if __name__ == '__main__':
    main()
