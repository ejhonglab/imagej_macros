
// Manually copy the contents of this file to the end of:
// <fiji directory>/macros/StartupMacros.fiji.ijm

// Note that you may need to change the hotkeys for some of these if other plugins /
// modifications to your ImageJ use some of these keys.

macro "Plot ROI time profile  [f1]" {
    // I copied this from section below, which seems kinda non-sensical and I'm not sure
    // where it came from, but I also kind of feel like I didn't write it?
	run("Plot Z-axis Profile", "Profile=time");
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

// To avoid accidentally closing images this way
macro "Do nothing [w]" {
}
