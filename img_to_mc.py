#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Minecraft Block Quantizer (Formerly Wool Quantizer)
"""
Created on Sat Aug  8 11:11:20 2020

@author: KyrasRhys

Parsing, dithering improvements, and general QOL changes courtesy of lmpynix
"""
# The goal of this script is to take a .jpg, downsample it by some integer factor...
# And then quantize using the average rgb value of some minecraft block textures
# These average values can seen down below in the dictionary 'blocks', with their corresponding blocks as keys
# From there, the quantized pixels are used to recreate the quantized image out of the corresponding minecraft block textures


import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import PIL.Image
import os.path as path
import argparse

# starting_dir = os.getcwd()
# texture_dir = starting_dir + "\\mc_textures"

# Downsample a one-dimensional array 'x' by an integer factor 'D'
def downsample(D, x):
    floor_len = int(len(x) // D)
    downsampled = np.asarray([x[D * i] for i in range(floor_len)])
    return downsampled

def main():
    parser = argparse.ArgumentParser(description="Convert an image into Minecraft pixel art.")
    parser.add_argument("input", help="Input image to convert.")
    parser.add_argument("-d", "--decimate", type=int, default=1, help="Decimation factor to make image smaller.")
    parser.add_argument("-o", "--output", help="Output filename.", default="mc.jpg")
    parser.add_argument("-i", "--interactive", action='store_true', help="Force interactive mode")
    parser.add_argument("-a", "--colorarray", default="./mc_textures/color_array_and_blocks.npz", help="File path of alternate texture color to use.")
    parser.add_argument("-t", "--texture_dir", default="./mc_textures/", help="Path to texture directory")
    args = parser.parse_args()
    img = plt.imread(path.abspath(args.input))
    input_blocks = np.load(path.abspath(args.colorarray), allow_pickle=True)
    colors_array = input_blocks['color_array']
    blocks = input_blocks['blocks'].item()

    process(args.interactive, args.decimate, img, colors_array, path.abspath(args.output), blocks, path.abspath(args.texture_dir))
    

def process(interactive, M, img, colors_array, output_name, blocks, texture_dir):
    if interactive:
        print(
            "Please enter the name of the output image. (i.e. test , cat_picture, etc)\nPlease do not include a file extention in the name of the image\nOutput will be a .jpg"
        )
        output_name = input()

        # Parks-MacClellan low pass filter before decimation
        print(
            "Please enter the factor you want the image downscaled by.\nInput should be a positive integer\nEnter 1 to keep original image size"
        )
        M = int(input())  # downscaling factor

    # Extract width and height of the input image
    n_rows, n_cols, _ = np.shape(img)
    # Can't downscale by a factor of 1, will not work!
    if not (M == 1):

        # Separate the image into color channels
        img_red = np.zeros((n_rows, n_cols))
        img_green = np.zeros((n_rows, n_cols))
        img_blue = np.zeros((n_rows, n_cols))

        for row in range(n_rows):
            for col in range(n_cols):
                img_red[row, col] = img[row, col, 0]
                img_green[row, col] = img[row, col, 1]
                img_blue[row, col] = img[row, col, 2]
        # Begin by low pass filtering, no ensure no aliasing after downsampling/decimation

        # Band frequencies are in normalized digital frequencies. Bandwith should be 1/5 width of passband
        filter_bands = [0, (1 / M), (1 / M) + (1 / (5 * M)), 1]
        # Passband followed by stopband. Low pass filter
        band_gains = [1, 0]

        lpf = signal.remez(25, filter_bands, band_gains, fs=2)

        # Initialize filtered color channel arrays
        red_filt = np.zeros((n_rows, n_cols))
        green_filt = np.zeros((n_rows, n_cols))
        blue_filt = np.zeros((n_rows, n_cols))

        # Low pass filtering over each row, then column.
        for row in range(n_rows):
            red_filt[row] = signal.convolve(img_red[row], lpf, "same")
            green_filt[row] = signal.convolve(img_green[row], lpf, "same")
            blue_filt[row] = signal.convolve(img_blue[row], lpf, "same")

        for col in range(n_cols):
            red_filt[:, col] = signal.convolve(red_filt[:, col], lpf, "same")
            green_filt[:, col] = signal.convolve(green_filt[:, col], lpf, "same")
            blue_filt[:, col] = signal.convolve(blue_filt[:, col], lpf, "same")

        img_filt = np.zeros((n_rows, n_cols, 3), dtype="int")

        # Recombine color channels and constrain to valid rgb values
        for row in range(n_rows):
            for col in range(n_cols):
                img_filt[row, col, 0] = red_filt[row, col]
                img_filt[row, col, 1] = green_filt[row, col]
                img_filt[row, col, 2] = blue_filt[row, col]

        img_filt = np.clip(img_filt, 0, 255)

        # Decimation aka downsampling
        red_n_rows = int(n_rows // M)
        red_n_cols = int(n_cols // M)

        img_dec = np.empty((red_n_rows, red_n_cols, 3), dtype=int)

        # Applies the 1 dimensional downsample only on every Mth row
        # Other rows are disregarded
        # Downsamples both width and height by a factor of M
        for row in range(red_n_rows):
            img_dec[row] = downsample(M, img_filt[M * row])

    else:
        # If not downsampling, we can just copy the image and shape values from earlier
        red_n_rows = n_rows
        red_n_cols = n_cols
        img_dec = np.copy(img)

    # Array to store the new rgb values after quantization. Mostly used to see if the script is behaving as expected
    img_wools = np.zeros((red_n_rows, red_n_cols, 3), dtype="int")
    img_wools2 = np.zeros((red_n_rows, red_n_cols, 3), dtype="uint8")

    # Array 16 times the size of img_wools in each direction
    # Where img_wools ends with a quantized pixel color, img_blocks has a corresponding 16x16 minecraft texture
    img_blocks = np.zeros((16 * red_n_rows, 16 * red_n_cols, 3), dtype="uint8")

    # Copying earlier array, as I will need to modify this array to dither properly
    # I want to keep the old array, so I can view it to check that the image was propely downsampled
    dec_error = np.copy(img_dec)
    # Needs to be an array of floats to add errors correctly
    dec_error = dec_error.astype(float)


    # Iterating over every pixel in the downscaled image
    total_pixels = red_n_rows * red_n_cols
    pixels_complete = 0
    for row in range(red_n_rows):
        if row % 2 == 0:
            for col in range(red_n_cols):
                pixel = np.clip(dec_error[row, col], 0, 255)
                r = int(round(pixel[0]))
                g = int(round(pixel[1]))
                b = int(round(pixel[2]))
                least_key = colors_array[r, g, b]

                # Concatenating with '.png' to open corresponding texture to block selected by quantizer
                texture = PIL.Image.open(path.join(texture_dir, least_key + ".png"))
                # Textures are RGBA, so need to conver to RGB first
                texture = np.asarray(texture.convert("RGB"))

                # img_blocks is basically an array of 16x16 square minecraft textures
                # the pixel indexes 'row' and 'col' correspond to a particular texture square in img_blocks
                # here, we are copying the corresponding texture to its portion of img_blocks
                img_blocks[16 * row : 16 * row + 16, 16 * col : 16 * col + 16] = texture

                # Calculating error to implement Atkinson dithering
                img_wools[row, col] = blocks[least_key]
                img_wools2[row, col] = blocks[least_key]
                error = pixel - img_wools[row, col]
                # Didn't want to spend too much time writing code to correct for the out of bound errors on the edge of the image...
                # So I'm just using try blocks here
                # Pixels along the right, left, and bottom edges may be slightly off
                try:
                    dec_error[row, (col + 1), 0] += 1 / 8 * error[0]
                    dec_error[row, (col + 1), 1] += 1 / 8 * error[1]
                    dec_error[row, (col + 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[row, (col + 2), 0] += 1 / 8 * error[0]
                    dec_error[row, (col + 2), 1] += 1 / 8 * error[1]
                    dec_error[row, (col + 2), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col - 1), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col - 1), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col - 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col + 1), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col + 1), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col + 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 2), (col), 0] += 1 / 8 * error[0]
                    dec_error[(row + 2), (col), 1] += 1 / 8 * error[1]
                    dec_error[(row + 2), (col), 2] += 1 / 8 * error[2]
                except:
                    pass
                pixels_complete += 1

                print('Percentage Completion:%.2f'%(100*pixels_complete/total_pixels), end="\r", flush=True)
        else:
            for col in range((red_n_cols - 1), -1, -1):
                pixel = np.clip(dec_error[row, col], 0, 255)
                r = int(round(pixel[0]))
                g = int(round(pixel[1]))
                b = int(round(pixel[2]))
                least_key = colors_array[r, g, b]

                # Concatenating with '.png' to open corresponding texture to block selected by quantizer
                texture = PIL.Image.open(path.join(texture_dir, least_key + ".png"))
                # Textures are RGBA, so need to conver to RGB first
                texture = np.asarray(texture.convert("RGB"))

                # img_blocks is basically an array of 16x16 square minecraft textures
                # the pixel indexes 'row' and 'col' correspond to a particular texture square in img_blocks
                # here, we are copying the corresponding texture to its portion of img_blocks
                img_blocks[16 * row : 16 * row + 16, 16 * col : 16 * col + 16] = texture

                # Calculating error to implement Atkinson dithering
                img_wools[row, col] = blocks[least_key]
                img_wools2[row, col] = blocks[least_key]
                error = pixel - img_wools[row, col]
                # Didn't want to spend too much time writing code to correct for the out of bound errors on the edge of the image...
                # So I'm just using try blocks here
                # Pixels along the right, left, and bottom edges may be slightly off
                try:
                    dec_error[row, (col - 1), 0] += 1 / 8 * error[0]
                    dec_error[row, (col - 1), 1] += 1 / 8 * error[1]
                    dec_error[row, (col - 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[row, (col - 2), 0] += 1 / 8 * error[0]
                    dec_error[row, (col - 2), 1] += 1 / 8 * error[1]
                    dec_error[row, (col - 2), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col + 1), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col + 1), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col + 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 1), (col - 1), 0] += 1 / 8 * error[0]
                    dec_error[(row + 1), (col - 1), 1] += 1 / 8 * error[1]
                    dec_error[(row + 1), (col - 1), 2] += 1 / 8 * error[2]
                except:
                    pass
                try:
                    dec_error[(row + 2), (col), 0] += 1 / 8 * error[0]
                    dec_error[(row + 2), (col), 1] += 1 / 8 * error[1]
                    dec_error[(row + 2), (col), 2] += 1 / 8 * error[2]
                except:
                    pass
                pixels_complete += 1
                print(
                    "Percentage Completion:%.2f"
                    % (100 * pixels_complete / total_pixels),
                    end="\r",
                    flush=True,
                )

    plt.imsave(output_name, img_blocks)

    print("\nDone!")

if __name__ == "__main__":
    main()
