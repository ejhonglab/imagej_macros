// Note that you may need to change the hotkeys for some of these if other plugins /
// modifications to your ImageJ use some of these keys.

// To avoid accidentally closing images this way
macro "Do nothing [w]" {
}

// Previously had this as a [s]->nothing, since I accidentally press [s] a lot, and
// never do it intentionally to actually save images.
// TODO maybe this should be [S], or something else that i'm less likely to hit by
// accident?
macro "Save ROIs [s]" {
    run("save rois");

    // TODO somehow use current RoiSet.zip path as file_path
    // Docs indicate I shouldn't need to deselect first here
    //print(getDirectory("image"));
    //print(getDirectory("image") + "RoiSet.zip");
    //roiManager("save", getDirectory("image"));

    // doesn't work w/o file_path argument
    //roiManager("save");
}

// Since I want to use this for overlay listener [p] -> plot_roi_responses binding.
// Replaces some kind of printing function I don't use.
macro "Do nothing [p]" {
}

// For plot_roi_responses(hallem=True), via overlay listener
// NOTE: [shift+h] did NOT work, but [H] did
macro "Do nothing [H]" {
}

// Overrides default 'draw' hotkey
macro "Do nothing [d]" {
}

// Didn't work (still deselected overlay ROI at least...)
//macro "Do nothing [backspace]" {
//}

macro "Plot ROI time profile  [f1]" {
	run("Plot Z-axis Profile", "Profile=time");

    // would prefer this if it was working (so i don't need to select raw.tif first)
	//run("t project in raw");
}

macro "Load experiment  [1]" {
	run("open experiment and rois", "mocorr_eval_only=true");
}

macro "Load experiment  [2]" {
	run("open experiment and rois", "mocorr_eval_only=false");
}

macro "Custom ROI overlay (with names)  [f3]" {
	run("overlay rois in curr z", "draw_labels=false draw_names=true black_behind_text=false");
}

macro "Custom ROI overlay  [f4]" {
	run("overlay rois in curr z", "draw_labels=false draw_names=false black_behind_text=false");
}

macro "Clear ROI overlay  [f5]" {
	run("Remove Overlay");
}

// TODO modify to not cause errors if no TIFFs matching if possible
macro "Close all traces [f6]" {
	close("*.tif-*-*");
}

macro "Overlay odors [f8]" {
    run("overlay odors");
}

// This macro is so that the default 'r' behavior (reverting image to unmodified state)
// doesn't also run when my keylistener in overlay_rois_in_curr_z.py triggers some
// behavior on '[r]'
macro "Update matching ROI [r]" {
}

// NOTE: [n] replaces the default hotkey that make a new stack (not sure why I'd want to
// do that though...)
macro "Number ROIs [n]" {
    run("number rois");
}

// f10 seems to open a menu whether i have a macro on it or not. maybe OS?
// f11-12 don't *seem* to do anything by default
macro "Restore window positions [f11]" {
    run("restore window positions");
}
macro "Save window positions [f12]" {
    run("save window positions");
}

