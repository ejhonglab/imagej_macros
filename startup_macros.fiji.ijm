
// Manually copy the contents of this file to the end of:
// <fiji directory>/macros/StartupMacros.fiji.ijm

// Note that you may need to change the hotkeys for some of these if other plugins /
// modifications to your ImageJ use some of these keys.

// To avoid accidentally closing images this way
macro "Do nothing [w]" {
}

// Since I accidentally press [s] a lot, and never do it intentionally to actually save
// images.
macro "Do nothing [s]" {
}

macro "Plot ROI time profile  [f1]" {
	run("Plot Z-axis Profile", "Profile=time");

    // would prefer this if it was working (so i don't need to select raw.tif first)
	//run("t project in raw");
}

macro "Load experiment  [f2]" {
	run("open experiment and rois");
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

// NOTE: [r] replaces the default hotkey that reverts image to unmodified state
macro "Update matching ROI [r]" {
    run("update matching roi");
}

// NOTE: [n] replaces the default hotkey that make a new stack (not sure why I'd want to
// do that though...)
macro "Number ROIs [n]" {
    run("number rois");
}
