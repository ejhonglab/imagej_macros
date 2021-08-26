
// Manually copy the contents of this file to the end of:
// <fiji directory>/macros/StartupMacros.fiji.ijm

macro "Custom ROI overlay  [f1]" {
	run("overlay rois in curr z", "draw_labels=false draw_names=false");
}

macro "Load experiment  [f2]" {
	run("open experiment and rois");
}
