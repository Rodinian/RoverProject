import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    
    #try to use the cv2 treshold 
    #convert into BGR
    R = img[:,:,0]
    G = img[:,:,1]
    B = img[:,:,2]
    img_BGR = cv2.merge([B,G,R])
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img_BGR, cv2.COLOR_BGR2HSV)
    # define range of Golden color in HSV
    lower_golden = np.array([10 ,100,100])
    upper_golden = np.array([30,255,245])
    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower_golden, upper_golden)
    color_select = 200*np.ones_like(img[:,:,:])
    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(color_select,color_select, mask= mask)

    img_grey = cv2.cvtColor(img_BGR, cv2.COLOR_BGR2GRAY)
    object_grey = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(img_grey,(5,5),0)
    _,navigable = cv2.threshold(blur,160,255,cv2.THRESH_BINARY)
    _,obstacle = cv2.threshold(blur,160,255,cv2.THRESH_BINARY_INV)
    _,sampleRocks = cv2.threshold(object_grey,10,255,cv2.THRESH_BINARY)
    
    return navigable, obstacle, sampleRocks

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    # Apply a rotation
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated
def throwUpHalf(img):
	width,height,depth = img.shape
	for i in range(1,depth):
		for j in range(1,width):
			for k in range(height/2,height):
				img[j,k,i] = 0
				
	return img

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    dst_size = 5 
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32(
                [[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - bottom_offset],[Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - bottom_offset],[Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],])
    # 2) Apply perspective transform
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image

    # 5) Convert map image pixel values to rover-centric coords
    # 6) Convert rover-centric pixel values to world coordinates
    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    Rover.img = throwUpHalf(Rover.img)
    navigable, obstacle, sampleRocks = color_thresh(Rover.img)
    warped_navigable = perspect_transform(navigable,source, destination)
    warped_obstacle = perspect_transform(obstacle,source, destination)
    warped_sampleRocks = perspect_transform(sampleRocks,source, destination)
    
    Rover.vision_image[:,:,0] = warped_obstacle
    Rover.vision_image[:,:,1] = warped_navigable
    Rover.vision_image[:,:,2] = warped_sampleRocks
    
    # Extract navigable terrain pixels
    navigable_xpix, navigable_ypix = rover_coords(warped_navigable)
    obstacle_xpix, obstacle_ypix = rover_coords(warped_obstacle)
    sampleRocks_xpix, sampleRocks_ypix = rover_coords(warped_sampleRocks)
  
    scale = 10

    # Get navigable pixel positions in world coords
    navigable_x_world, navigable_y_world = pix_to_world(navigable_xpix,navigable_ypix, Rover.pos[0], Rover.pos[1], Rover.yaw, 200, scale)
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_xpix, obstacle_ypix, 
                                    Rover.pos[0], Rover.pos[1], Rover.yaw, 
                                    Rover.ground_truth.shape[0], scale)
    rock_x_world, rock_y_world = pix_to_world(sampleRocks_xpix, sampleRocks_ypix, 
                                    Rover.pos[0], Rover.pos[1], Rover.yaw, 
                                    Rover.ground_truth.shape[0], scale)

    Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 50
    Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
    Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 10
    
    
    #8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles
    dist, angles = to_polar_coords(navigable_xpix, navigable_ypix)
    Rover.nav_dists = np.mean(dist)
    Rover.nav_angles = np.mean(angles)
    return Rover