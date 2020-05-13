import cv2
import numpy as np
from display_utils import *

A = 0.75
B = 1.25

def render_circle(mask, cx, cy, radius):
    y,x = np.ogrid[-radius:radius, -radius:radius]
    index = x**2 + y**2 <= radius**2
    mask[cy-radius:cy+radius, cx-radius:cx+radius][index] = 1

def render_butterworth_curve(mask, radius):
    sy,sx = mask.shape
    radius2 = radius ** 2
    sx /= 2
    sy /= 2
    y,x = np.ogrid[-sy:sy, -sx:sx]
    x2 = x ** 2
    y2 = y ** 2
    mask[:,:] = 1 / (1 + ((x2 + y2) / radius2) ** 3)

def render_gaussian_curve(mask, radius):
    sy,sx = mask.shape
    radius2 = 2 * (radius ** 2)
    sx /= 2
    sy /= 2
    y,x = np.ogrid[-sy:sy, -sx:sx]
    x2 = x ** 2
    y2 = y ** 2
    mask[:,:] = np.exp(-(x2 + y2) / radius2)


img = cv2.imread('trees.jpg')
orig_img = np.copy(img)
img = np.sum(img, 2) / 3
img = np.log1p(img)

fft = np.fft.fft2(img)
fshift = np.fft.fftshift(fft)

cutoff_radius = 2

def scale(thing, clip=True):
    if clip:
        thing = np.maximum(0, np.minimum(thing, 255))
    else:
        thing -= np.min(thing)
        thing /= np.max(thing)
        thing *= 255
    thing = thing.astype(np.uint8)
    return thing

def apply_mask(mask):
    masked_fshift = (A + B * mask) * fshift
    return scale(
            np.exp(
                np.real(
                    np.fft.ifft2(
                        np.fft.ifftshift(masked_fshift)))) - 1)

def ideal(radius = cutoff_radius):
    mask = np.zeros(img.shape, np.uint8)
    center_x = img.shape[1] // 2
    center_y = img.shape[0] // 2
    render_circle(mask, center_x, center_y, radius)
    rmask = np.uint8(mask != 1)
    return (
        rmask * 255, apply_mask(rmask),
    )

def butterworth(radius = cutoff_radius):
    mask = np.zeros(img.shape, np.float)
    render_butterworth_curve(mask, radius)
    rmask = 1 - mask
    return (
        np.uint8(rmask * 255), apply_mask(rmask),
    )

def gaussian(radius = cutoff_radius):
    mask = np.zeros(img.shape, np.float)
    render_gaussian_curve(mask, radius)
    rmask = 1 - mask
    return (
        np.uint8(rmask * 255), apply_mask(rmask),
    )


cv2.namedWindow('Output', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Output', 1000, 1000)

view = nxm_matrix_view(range(6), ['ideal', 'butterworth', 'gaussian'], 1, 2)
cv2.imshow('Output', side_by_side(
    layout_with_names({
        "Homomorphic Fourier Filters - AliMPFard": Horizontal(6,6),
        '': view,
    }, Vertical), *ideal(), *butterworth(), *gaussian(), orig_img
))


wait_for_key('q', lambda: cv2.waitKey(0), cv2.destroyAllWindows)
