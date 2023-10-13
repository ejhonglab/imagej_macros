
from os.path import join, split, exists, isdir
from zipfile import ZipFile
import tempfile
from shutil import rmtree
import glob

from ij import IJ, WindowManager
from ij.plugin.frame import RoiManager


# NOTE: copied to ijroi module, but can't easily share until proper python (w/ modules)
# is supported in ImageJ
def zip_contents_equal(filename1, filename2):
    """
    Compare two ZipFiles to see if they would expand into the same directory structure
    without actually extracting the files.

    From RootTwo's answer at https://stackoverflow.com/questions/66524269
    """
    BUFSIZE = 1024

    with ZipFile(filename1, 'r') as zip1, ZipFile(filename2, 'r') as zip2:

        # Index items in the ZipFiles by filename. For duplicate filenames, a later
        # item in the ZipFile will overwrite an ealier item; just like a later file
        # will overwrite an earlier file with the same name when extracting.
        zipinfo1 = {info.filename:info for info in zip1.infolist()}
        zipinfo2 = {info.filename:info for info in zip2.infolist()}

        # Do some simple checks first
        # Do the ZipFiles contain the same the files?
        if zipinfo1.keys() != zipinfo2.keys():
            return False

        # Do the files in the archives have the same CRCs? (This is a 32-bit CRC of the
        # uncompressed item. Is that good enough to confirm the files are the same?)
        if any(zipinfo1[name].CRC != zipinfo2[name].CRC for name in zipinfo1.keys()):
            return False

        # Skip/omit this loop if matching names and CRCs is good enough.
        # Open the corresponding files and compare them.
        for name in zipinfo1.keys():

            # 'ZipFile.open()' returns a ZipExtFile instance, which has a 'read()'
            # method that accepts a max number of bytes to read. In contrast,
            # 'ZipFile.read()' reads all the bytes at once.
            with zip1.open(zipinfo1[name]) as file1, zip2.open(zipinfo2[name]) as file2:

                while True:
                    buffer1 = file1.read(BUFSIZE)
                    buffer2 = file2.read(BUFSIZE)

                    if buffer1 != buffer2:
                        return False

                    if not buffer1:
                        break

        return True


def main():
    verbose = False

    n_open_images = WindowManager.getImageCount()
    if n_open_images == 0:
        return

    imp = IJ.getImage()
    # Will actually fail with an ugly error before this (at least if nothing is open,
    # maybe not if we just have something else selected?)
    if imp is None:
        return

    # NOTE: docs say this could return instance to a hidden "batch mode" RoiManager,
    # if a "batch mode macro" is currently running and regular ROI manager is not open.
    # I'm assuming this isn't likely to be happening/interfere with my use.
    manager = RoiManager.getInstance()
    if manager is None:
        return

    rois = manager.getRoisAsArray()
    # TODO might need to length-1 ROI list too
    if len(rois) == 0:
        return

    file_info = imp.getOriginalFileInfo()
    analysis_dir = file_info.directory


    # TODO replace this hack to find RoiSet.zip path w/ something that sets path to ROIs
    # in my open_experiment_and_rois.py script (though i had tried a few times to figure
    # out how i might store global state from jython, but i can't seem to find a
    # reliable way to do so, or at least no well documented mechanism)
    sep = '/'
    parts = [x for x in analysis_dir.split(sep) if len(x) > 0]

    # Since the filtering of empty parts will remove any slashes at start, but we would
    # need that initial seperator for a valid path.
    if analysis_dir.startswith(sep):
        parts = [''] + parts

    # TODO comment explaining why we have this expectation
    # NOTE: this was triggered once on 2023-09-29, analyzing 2023-06-23/1 data
    assert '..' == parts[-1], parts[-1]

    exp_dir = sep.join(parts[:-1])
    assert isdir(exp_dir), ('%s was not a directory!' % exp_dir)
    if verbose:
        print 'exp_dir:', exp_dir

    fly_analysis_dir, exp_dir_name = split(exp_dir)

    # TODO also warn / err if not using first (numbered? time recorded? should be
    # same...) diagnostic recording dir
    #
    # Should typically be 'glomeruli_diagnostics' exactly, though might occasionally be
    # something like 'glomeruli_diagnostics_redo'.
    # More recently, I've been doing 'diagnostics1', 'diagnostics2', etc (as I have more
    # odors and need to break it up across more recordings).
    if 'diag' not in exp_dir_name:
        # If we don't have any diagnostics for this fly, then OK to use current
        # directory.
        all_fly_exp_dirs = glob.glob(join(fly_analysis_dir, '*/'))

        # TODO replace w/ warning popup?
        # i forget if errors caused issues w/ subsequent jython calls...
        #
        # d[:-1] to remove trailing '/' before splitting
        # (otherwise we'd get empty string instead of directory name)
        assert not any(['diag' in split(d[:-1])[-1] for d in all_fly_exp_dirs]), \
            ('if diagnostic recordings exist, ROIs should be defined on first of those.'
            ' if you wish, manually save ROIs to appropriate diagnostic recording dir.'
        )

    roiset_path = join(exp_dir, 'RoiSet.zip')
    if verbose:
        print 'roiset_path:', roiset_path

    # TODO TODO option to backup to some (hidden?) folder?
    # (maybe don't save more often than some interval?)

    if exists(roiset_path):
        if verbose:
            print 'ROI zip', roiset_path, 'existed'

        # TemporaryDirectory not in Python 2.7 (assuming not in Jython either)
        temp_roiset_dir = tempfile.mkdtemp()
        assert isdir(temp_roiset_dir)

        temp_roiset_path = join(temp_roiset_dir, 'new_RoiSet.zip')
        assert not exists(temp_roiset_path)

        manager.runCommand('Save', temp_roiset_path)

        # Intially tried filecmp.cmp, but ZIP files contain timestamps for each item it
        # seems (and it seems ImageJ might set these all to current time)
        rois_unchanged = zip_contents_equal(roiset_path, temp_roiset_path)

        # TODO make sure this happens regardless of success of runCommand above
        rmtree(temp_roiset_dir)

        # So that mtime of roiset_path's file is not changed unless ROIs change,
        # since I use mtime of ROIs to decide if I need to re-run ROI based analyses.
        if rois_unchanged:
            if verbose:
                print 'ROIs unchanged!'

            return

    # All ROIs will be saved. Does not matter if we have ROI(s) selected (either via my
    # overlay or via ROI manager list)
    # TODO TODO test behavior in case only 1 ROI is in list
    # TODO include time written?
    manager.runCommand('Save', roiset_path)
    print 'saved ROIs to %s' % roiset_path


if __name__ == '__main__':
    main()

