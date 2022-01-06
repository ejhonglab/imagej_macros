
from ij import IJ, WindowManager
from ij.gui import Overlay, Roi

# NOTE: not quite working


def main():
    curr_image = WindowManager.getCurrentImage()

    window_title = 'raw.tif'
    #window = WindowManager.getWindow(window_title)
    #if window is None:
    #    print 'no window with title', window_title
    #    return

    #WindowManager.toFront(window)

    IJ.selectWindow(window_title)

    roi = curr_image.roi
    if roi is None:
        print 'no active ROI'
        return

    image = window.getImagePlus()

    roi = roi.clone()
    roi.setImage(image)

    IJ.run('Plot Z-axis Profile', 'Profile=time')


if __name__ == '__main__':
    main()

