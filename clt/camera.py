import ctypes
import ctypes.util as Cutil
import numpy as np
import atexit

interface_name = 'img0'
imaqlib_path = Cutil.find_library('imaq')
imaq = ctypes.windll.LoadLibrary(imaqlib_path)


class IMAQError(Exception):
    """Errors produced while calling National Intrument's IMAQ functions.
    Produces textual error message that corresponds to a specific code."""

    def __init__(self, code):
        self.code = code
        text = ctypes.c_char_p('')
        imaq.imgShowError(code, text)
        self.message = "{}: {}".format(self.code, text.value)
        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, self.message)


def imaq_error_handler(code):
    """Print textual error message that is associated with the error code."""

    if code < 0:
        raise IMAQError(code)
        free_associated_resources = 1
        imaq.imgSessionStopAcquisition(session_id)
        imaq.imgClose(session_id, free_associated_resources)
        imaq.imgClose(interface_id, free_associated_resources)
    else:
        return code

# START C MACROS DEFINITIONS
# define some C preprocessor macros
# (these are all defined in the niimaq.h file)
_IMG_BASE = 0x3FF60000

IMG_BUFF_ADDRESS = _IMG_BASE + 0x007E  # void *
IMG_BUFF_COMMAND = _IMG_BASE + 0x007F  # uInt32
IMG_BUFF_SIZE = _IMG_BASE + 0x0082  # uInt32
IMG_CMD_STOP = 0x08  # single shot acquisition
IMG_CMD_LOOP = 0x02  # continuous acquisition
IMG_ATTR_ROI_WIDTH = _IMG_BASE + 0x01A6
IMG_ATTR_ROI_HEIGHT = _IMG_BASE + 0x01A7
IMG_ATTR_BYTESPERPIXEL = _IMG_BASE + 0x0067
IMG_ATTR_COLOR = _IMG_BASE + 0x0003  # true = supports color
IMG_ATTR_PIXDEPTH = _IMG_BASE + 0x0002  # pix depth in bits
IMG_ATTR_BITSPERPIXEL = _IMG_BASE + 0x0066  # aka the bit depth

IMG_BAYER_PATTERN_GBGB_RGRG = 0
IMG_BAYER_PATTERN_GRGR_BGBG = 1
IMG_BAYER_PATTERN_BGBG_GRGR = 2
IMG_BAYER_PATTERN_RGRG_GBGB = 3
# END C MACROS DEFINITIONS

# this is not an exhaustive list, merely the ones used in this program
imaq_function_list = [
    imaq.imgGetAttribute,
    imaq.imgInterfaceOpen,
    imaq.imgSessionOpen,
    imaq.niimaquDisable32bitPhysMemLimitEnforcement,  # because we're running on a 64-bit machine with over 3GB of RAM
    imaq.imgCreateBufList,
    imaq.imgCreateBuffer,
    imaq.imgSetBufferElement,
    imaq.imgSnap,
    imaq.imgSessionSaveBufferEx,
    imaq.imgSessionStopAcquisition,
    imaq.imgClose,
    imaq.imgCalculateBayerColorLUT,
    imaq.imgBayerColorDecode]

# for all imaq functions we're going to call, we should specify that if they
# produce an error (a number), we want to see the error message (textually)
for func in imaq_function_list:
    func.restype = imaq_error_handler


# open interface
interface_id = ctypes.c_uint32()
session_id = ctypes.c_uint32()
buffer_list_id = ctypes.c_uint32()

width, height = ctypes.c_uint32(), ctypes.c_uint32()
(has_color, pixdepth, bitsperpixel,
 bytes_per_pixel) = [ctypes.c_uint8() for _ in range(4)]

imaq.imgInterfaceOpen(interface_name, ctypes.byref(interface_id))
imaq.imgSessionOpen(interface_id, ctypes.byref(session_id))

# poll the camera (or is it the camera file (icd)?) for these attributes and
# store them in the variables
for var, macro in [(width, IMG_ATTR_ROI_WIDTH),
                   (height, IMG_ATTR_ROI_HEIGHT),
                   (bytes_per_pixel, IMG_ATTR_BYTESPERPIXEL),
                   (pixdepth, IMG_ATTR_PIXDEPTH),
                   (has_color, IMG_ATTR_COLOR),
                   (bitsperpixel, IMG_ATTR_BITSPERPIXEL)]:
    imaq.imgGetAttribute(session_id, macro, ctypes.byref(var))

print("Image ROI size: {} x {}".format(width.value, height.value))
print("Pixel depth: {}\nBits per pixel: {} -> {} bytes per pixel".format(pixdepth.value,
                                                                         bitsperpixel.value,
                                                                         bytes_per_pixel.value))
bufsize = width.value*height.value*bytes_per_pixel.value

imaq.niimaquDisable32bitPhysMemLimitEnforcement(session_id)

# Creates a buffer list with one buffer
imaq.imgCreateBufList(1, ctypes.byref(buffer_list_id))

imgbuffer = ctypes.POINTER(ctypes.c_uint16)()  # create a null pointer

# allocate memory (the buffer) on the host machine (param2==0)
imaq.imgCreateBuffer(session_id, 0, bufsize, ctypes.byref(imgbuffer))

# my guess is that the cast to an uint32 is necessary to prevent 64-bit
# callable memory addresses
imaq.imgSetBufferElement2(buffer_list_id, 0, IMG_BUFF_ADDRESS,
                         ctypes.cast(imgbuffer,
                                     ctypes.POINTER(ctypes.c_uint32)))

imaq.imgSetBufferElement2(buffer_list_id, 0, IMG_BUFF_SIZE, bufsize)
imaq.imgSetBufferElement2(buffer_list_id, 0, IMG_BUFF_COMMAND, IMG_CMD_LOOP)


def start_continuous_acquisition():
    imaq.imgMemLock(buffer_list_id)
    imaq.imgSessionConfigure(session_id, buffer_list_id)
    imaq.imgSessionAcquire(session_id, True, None)
    pass


def close_everything():
    print('Closing camera')
    free_associated_resources = 1
    imaq.imgSessionStopAcquisition(session_id)
    imaq.imgClose(session_id, free_associated_resources)
    imaq.imgClose(interface_id, free_associated_resources)

atexit.register(close_everything)


def get_image():
    curr_buff_number = ctypes.c_int()
    current_buffer = ctypes.POINTER(ctypes.c_void_p)()
    imaq.imgSessionExamineBuffer2(session_id, 0, ctypes.byref(curr_buff_number),
                                  ctypes.byref(current_buffer))
    np_buffer = np.core.multiarray.int_asbuffer(ctypes.addressof(current_buffer.contents), bufsize)
    image = np.reshape(np.frombuffer(np_buffer, np.uint16),
                       (height.value, width.value)).T
    image_copy = np.array(image)
    imaq.imgSessionReleaseBuffer(session_id)
    return image_copy