# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 14:27:00 2020

@author: Obmuw
"""
import multiprocessing

import numpy as np

#This script is intended to be used to precompute the nearest colored minecraft block (out of a given list) for every integer rgb value in the color space
#Nearest meaning least euclidian distance, if we consider r,g, and b to represent orthoganal axis of 3-d euclidan space
#Saves the dictionary 'blocks' as 'blocks.npy'
#Saves the array containing the nearest blocks for all integer rgb values as 'color_array_fin.npy'



#Euclidian Norm for finding closest points in RGB color space
#Its actually the 
def norm(x):
    sq_sum = 0
    for i in range(len(x)):
        sq_sum += x[i]**2
        
    return sq_sum



#A dictionary of minecraft blocks and their average rgb color values
#Note: Block names should take the same formatting as their corresponding textures's names
#i.e. white_wool.png gets the key white_wool in this dictionary
#The rgb color values don't nessicarily need to be the average color of the block, they should just be representative of its color
blocks = {
    'white_wool':[233,236,236],
    'orange_wool':[240,118,19],
    'magenta_wool':[189,68,179],
    'light_blue_wool':[58,175,217],
    'yellow_wool':[248,198,39],
    'lime_wool':[112,185,25],
    'pink_wool':[237,141,172],
    'gray_wool':[62,68,71],
    'light_gray_wool':[142,142,134],
    'cyan_wool': [21,137,145],
    'purple_wool':[121,42,172],
    'blue_wool':[53,57,157],
    'brown_wool':[114,71,40],
    'green_wool':[84,109,27],
    'red_wool':[161,39,34],
    'black_wool':[20,21,25],
    'bricks':[151,98,83],
    'light_blue_concrete':[36,137,199],
    'blue_concrete':[45,47,143],
    'lapis_block':[37,67,140],
    'pink_concrete':[214,101,143],
    'gray_concrete':[55,58,62],
    'black_concrete':[8,10,15],
    'cyan_concrete':[21,119,136],
    'white_concrete':[207,213,214],
    'orange_concrete':[224,97,1],
    'red_concrete':[142,33,33],
    'yellow_concrete':[241,174,21],
    'red_terracotta':[143,61,47],
    'red_sand':[191,103,33],
    'warped_planks':[43,105,99],
    'green_concrete':[73,91,36],
    'end_stone':[220,223,158],
    'oak_planks':[162,131,79],
    'spruce_planks':[115,85,49],
    'birch_planks':[192,175,121],
    'acacia_planks':[168,90,50],
    'jungle_planks':[160,151,81],
    'redstone_block':[176,25,5],
    'sand':[219,207,163],
    'iron_block':[220,220,220],
    'bedrock':[85,85,85],
    'diamond_block':[98,237,228],
    'black_terracotta':[37,23,16],
    'chiseled_stone_bricks':[120,119,120],
    'magenta_concrete':[169,48,159],
    'sponge':[196,192,75],
    'sandstone':[216,203,156],
    'dirt':[134,96,67],
    'gold_block':[246,208,61],
    'orange_terracotta':[162,84,38],
    'blue_terracotta':[74,60,91]
    }



def c_array_comp(n,m,q):
    #Splits the RBG color space into m layers, where g and b take their full range 0 to 255, while each layer takes on a range of 256//m values
    #Calculates the nearest color minecraft block for all integer rgb vales in the nth layer
    #q is a queue, to which the function adds a tuple containg n and the nth layer of the array of nearest blocks
    div = int(256//m)
    array = np.empty((div,256,256),dtype='object')
    for red in range(div):
        for blue in range(256):
            for green in range(256):
                nearest_block = 'white_wool'
                shortest_dist = 256**3
                for key in blocks:
                    #Calculating the distance between a color in the rgb color space and the average colors of each minecraft block
                    dist = norm(np.array([(red+div*n),green,blue])-blocks[key])
                    if dist <shortest_dist:
                        shortest_dist = dist
                        nearest_block = key
                #Writing the nearest block to the array
                array[red,green,blue] = nearest_block
    q.put((n,array))   


def color_comp(m):
    #m being the number of hardware threads the program should run on
    if not(256%m==0):
        print('m must evenly divide 256')
        return
    else:
        q = multiprocessing.Manager().Queue()
        processes = []
        for i in range(m):
            p = multiprocessing.Process(target=c_array_comp,args=(i,m,q))
            processes.append(p)
            p.start()
        
    for process in processes:
        process.join()
    
    color_array = np.empty((256,256,256),dtype='object')   
    div = int(256//m)
    
    
    #Stitching the arrays back together to create an array containing the nearest minecraft blocks for integer values in the rgb color space
    #Since we don't know the order the layers go onto the queue, we extract the layer number as x and copy it to the corresponding portion of color_array
    for i in range(m):
        x, partial_array = q.get(0)
        color_array[(div*x):(div*x+div)] = partial_array
        
    return color_array

if __name__ == '__main__':
    ca = color_comp(4)
    np.save('blocks.npy',blocks)
    np.save('color_array_fin.npy',ca)
