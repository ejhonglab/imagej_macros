
These scripts are mainly quality-of-life improvements for my workflow using the builtin
ImageJ ROI manager to define volumetric ROIs (on movies with a Z dimension).

The main improvement is a script to overlay ROIs only in the Z-plane they are defined
in, rather than the promiscuous `Show All` function in the ROI manager.

In the ROI Manager `Options` menu there is an option called `Associate "Show All" ROIs
with slices`, but then it seems the overlays are specific to the combination of the time
and Z-index, and I wanted to see the ROIs as I scrolled through the time axis of the
movie.


### Installation

```
git clone https://github.com/ejhonglab/imagej_macros
```

#### Linux (and maybe Mac?)

```
./imagej_macros/install.sh
```

The above command will make symbolic links to all the `*.py` files in this repo under
the Fiji `plugins` folder. Restart Fiji.


#### Windows

Manually copy all of the `*.py` files from this repo to the `Fiji.app/plugins` folder of
your Fiji installation. Restart Fiji.


#### Setting up hotkeys

Manually copy the contents of `imagej_macros/startup_macros.fiji.ijm` to the end of the
`Fiji.app/macros/StartupMacros.fiji.ijm`. Mind potential conflicts between these
shorcuts and other plugins / modifications you have, changing if needed. Restart Fiji.

Current hotkeys:
- `[f1]`: plot time profile of selected ROI

- `[f2]`: opens `raw.tif` and ROI manager ROIs in a `RoiSet.zip` from within selected directory

- `[f3]`: overlays ROIs with names, only drawing them in the planes they are defined in,
  for movies with a Z dimension

- `[f4]`: same as above, but without drawing ROI labels

The corresponding scripts installed above should also be available towards the bottom of
the `Plugins` menu (not under a sub-menu).

