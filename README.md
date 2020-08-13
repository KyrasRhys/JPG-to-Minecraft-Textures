# JPG-to-Minecraft-Textures
Simple python script for reproducing a jpg image out of a set of minecraft textures, with Atkinson dithering. Optional image decimation before conversion.

The purpose of this script is to take an input image, downscale it (optional), and then quantize each pixel against the average colors of some pre-selected minecraft block textures. During quantization, the error at each pixel is distributed to neighboring pixels via the Atkinson dithering algorithm. From there, the dithered image is reconstructed pixel by pixel from the relevant minecraft textures.

The resulting image acts as a useful reference when constructing minecraft pixel art, as well as just being interesting to look at.

To generate the final image, the script ('jpg_to_mc.py') opens the file 'blocks.npy' in the folder 'mc_textures'. 'blocks.npy' is a dictionary wrapped in a numpy array that uses the names of each block used as keys that link to the block's average corresponding rgb values. To save time, 'jpg_to_mc.py' does not directly computed the closest colored minecraft block at each pixel directly. Instead, the script opens 'color_array_fin.npy' in 'mc_textures', which is a numpy object array of size (256,256,256). The indices of each elemet of that array correspond to a particular rgb color, and each element of the array correspond to the name of the minecraft block closest in color to the given rgb index. Both of these files are generated using 'color_precomputation.py'. Be aware that this file can take quite a while to run.


To replace them (effectively changing the set of textures used to generate every image), modify the dictionary 'blocks' in 'color_precomputation.py' with the name of the blocks you want and their corresponding average rgb colors. From there, simply run 'color_precompuation.py', and either place the resulting files in 'mc_textures', or pass their locations as arguements when running 'jpg_to_mc.py'.

NOTE: The names of the keys in 'blocks' must correspondind directly to the names of the relevant textures. (i.e. white_wool.png corresponds to the key name 'white_wool'.)

The relevant minecraft textures have not been provided in this repository, but they can be found fairly easily by opening minecraft.jar with file archiving software.

The minecraft textures used in the given .npy files are:
    'white_wool'
    'orange_wool'
    'magenta_wool'
    'light_blue_wool'
    'yellow_wool'
    'lime_wool'
    'pink_wool'
    'gray_wool'
    'light_gray_wool'
    'cyan_wool'
    'purple_wool'
    'blue_wool'
    'brown_wool'
    'green_wool'
    'red_wool'
    'black_wool'
    'bricks'
    'light_blue_concrete'
    'blue_concrete'
    'lapis_block'
    'pink_concrete'
    'gray_concrete'
    'black_concrete'
    'cyan_concrete'
    'white_concrete'
    'orange_concrete'
    'red_concrete'
    'yellow_concrete'
    'red_terracotta'
    'red_sand'
    'warped_planks'
    'green_concrete'
    'end_stone'
    'oak_planks'
    'spruce_planks'
    'birch_planks'
    'acacia_planks'
    'jungle_planks'
    'redstone_block'
    'sand'
    'iron_block'
    'bedrock'
    'diamond_block'
    'black_terracotta'
    'chiseled_stone_bricks'
    'magenta_concrete'
    'sponge'
    'sandstone'
    'dirt'
    'gold_block'
    'orange_terracotta'
    'blue_terracotta'

This script was written in python 3.7.6 by myself, with improvements from lmpynix on i/o, dithering, and general usability improvements.
It depends upon the following python modules: numpy, scipy.signal, matplotlib.pyplot, PIL.Image, os.path, argparse, and multiprocessing.
