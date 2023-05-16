# Written by Jan Brascamp 9/29 and edited by Haley Frey
# Last edited on 2/20/13

# ------ File Description ------
""" This script creates slow change stimuli from sets of photoshopped cartoon images. 
	* Prior to running this script, generate in photoshop and save component versions of the images
		- This code expects .jpg files named in the format Img#_OneColor_quickChange1State1_quickChange2State1.jpg. They can be named anything as long as each portion between '_' is unique. These can be numbers or text. To be human readable, we used brief descriptions of the change.
		- Example: Img01_Orange_yesWindow_noFlower.jpg
		- This code expects these files to be located in a folder named firstColor_secondColor. It is designed to create morphs between only two colors at a time (example: yellow and orange). The same component images can be used for additional morphs (example: yellow-blue) as long as they are moved to a folder titled Yellow_Blue
		- To create morphs between Orange and Yellow, ensure that all images have been named correctly and are in a folder named Orange_Yellow (or Yellow_Orange - the order does not matter, the code will choose the color direction randomly). The code will run into errors if any images are missing.
		- While this code is designed to handle only one color combination at a time, it can handle multiple different images of the same color morph at one time. Simple put all component images for each Img (for example: Img01, Img02, Img05) into the same color named folder and ensure the names follow the format of image number, color, and quick changes
	* Make sure to install the .yaml or ensure all of the necessary packages are installed (see Imports)
	* Download and install ffmpeg and either add to PATH or move to a convenient location https://ffmpeg.org/
""" 

# ------ Imports ------
import os
from PIL import Image
import numpy
import re
import subprocess

# ------ Global Variables ------
morph_length_seconds = 16	# how long the morph will take place over
steps_per_second_video = 12	# how many frames per second should ffmpeg string together for the video
number_of_morph_steps = morph_length_seconds * steps_per_second_video	# how many frames are needed for the slow color change
no_change_in_seconds = 2	# how many seconds of no changes at the beginning and end of the video
no_change_in_frames = no_change_in_seconds * steps_per_second_video	# how many frames are needed to achieve no_change_in_seconds of no changes at start and end of video; based on no_change_in_seconds and steps_per_second_video
quick_change_time_section_proportion = 0.75	# each quick change occurs at a random moment within a designated section of the sequence. For instance, if there is only one quick change, then that section is the full sequence itself; if there are two quick changes, then the sections in which those changes occur are the first 0.5 and the second 0.5, respectively. For three it is the first 1/3, the second 1/3, and the third 1/3. The variable right here makes it so that the changes can only occur within a central proportion, defined here, of those sections. The reason is it avoids simultaneous changes (e.g. when change one is at the very last moment of the first section and change two is at the very first moment of the second section).
quick_change_length_frames = steps_per_second_video	# how many frames the quick change will last (make sort of gradual instead of very abrupt) currently set to steps_per_second_video because we always want it to last 1s
change_step = 1 / (quick_change_length_frames + 1)	# how many steps/frames the quick changes should last
color = 'Yellow_Orange'	# name of the folder where the photoshopped component images to be used for these morphs are. This code is designed to be run for one color pair at a time and make sure to name the folder this color

# ------ Paths ------
jpg_path = '/Users/haleyfrey/Dropbox/MakeMovies/SlowChangeImages/' + color	# the location of the images that form the basis of the animations
temp_path = '/Users/haleyfrey/Dropbox/MakeMovies/create_slow_change_scenes/temp/'	# location where we temporarily put frames that are then assembled to create the slow change sequences; will be created later if it does not already exist
morph_path = '/Users/haleyfrey/Dropbox/MakeMovies/create_slow_change_scenes/morph_frames/'	# location where the set of frames to be converted to video will be saved
output_path = '/Users/haleyfrey/Dropbox/MakeMovies/create_slow_change_scenes/final_videos/'	# location where the final videos and README will be saved
ffmpeg_path = '/Applications/ffmpeg'	# location of ffmpeg; if ffmpeg has been added to PATH, ffmpeg_path can be equal to just 'ffmpeg'

try:
	os.mkdir(temp_path)			# create the temporary path...
except:
	pass						# ...and don't throw an error if it already exists

try:
	os.mkdir(morph_path)		# create the output path...
except:
	pass						# ...and don't throw an error if it already exists

try:
	os.mkdir(output_path)		# create the output path...
except:
	pass						# ...and don't throw an error if it already exists

# ------ Main Body of Script ------
""" 1. Read in all component image files for each Img (that will become a video). Determine slow change states, number of quick changes, and quick change states. """
jpg_file_names = [element for element in os.listdir(jpg_path) if '.jpg' in element] # select all jpg images in jpg_path
filename_roots = list(set([this_file_name.split('_')[0] for this_file_name in jpg_file_names]))	# among all jpg_files, list of all unique strings that come before the first '_', aka which image it is. E.g., "Img01"

for filename_root in filename_roots:	# go over all those unique strings that can come before the fist '_' (loop through all images in folder)

	print('working on file ' + filename_root)

	these_file_names = [one_file_name for one_file_name in jpg_file_names if one_file_name.split('_')[0] == filename_root]	# select all file names that have that string in that position

	slow_change_options = [color.split('_')[0], color.split('_')[1]]	# the two options for the slow change; NOTE: make sure that the files are named accordingly with the color name occuring after the first "_"; because this code expects to be run for a single color combination at a time, the color variable can be used to obtain the slow change states
	numpy.random.shuffle(slow_change_options)	# shuffling the slow_change_options randomizes which direction the morph occurs. to keep this standard (and matching the folder name), simply comment out this line
	
	num_quick_changes = len(these_file_names[0].split('_')) - 2	# how many quick changes are there? the number of quick changes is determined by the options in the file name: after the Img# and slow color option, the quick change options are listed and separated by "_"
	all_quick_change_options = []		# make a list of pairs of values, with each pair being the two values that a given quick-change property can take (e.g. Window and Nowin), and the length of the list being equal to the number of quick changes (so num_quick_changes); later this will be shuffled to randomize the order of the quick changes
	quick_changes_in_name_order = []	# this will contain the same information as all_quick_change_options but will be used for building up the names of the files

	for quick_change_index in range(num_quick_changes):
		these_quick_change_options = list(set([this_file_name.split('_')[quick_change_index + 2] for this_file_name in these_file_names]))
		all_quick_change_options += [[one_option.split('.')[0] for one_option in these_quick_change_options]]

		quick_changes_in_name_order += [[one_option.split('.')[0] for one_option in these_quick_change_options]]
	
	numpy.random.shuffle(all_quick_change_options)	# allows the changes to occur in a random order. for nonrandom order, uncomment this line. this will result in the changes occuring in the order they are presented in the file name

	# Write details of each video to a README text file
	# code adapted from https://thispointer.com/how-to-append-text-or-lines-to-a-file-in-python/
	readme_filename = 'README.txt'
	with open(os.path.join(output_path, readme_filename),"a+") as readme_file:
		readme_file.seek(0)	# move read cursor to the start of file.
		data = readme_file.read(100)	# if file is not empty then append '\n'
		if len(data) > 0 :
			readme_file.write("\n")

		# Append text at the end of file
		readme_file.write('This slow change video is of ' + filename_root + '.\n')
		readme_file.write('The beginning color is ' + slow_change_options[0] + ' and the ending color is ' + slow_change_options[1] + '.\n')
		readme_file.write('There are ' + str(num_quick_changes) + ' quick changes which occur as follows:\n')
		for one_change in range(num_quick_changes):
			readme_file.write(all_quick_change_options[one_change][0] + ' changes to ' + all_quick_change_options[one_change][1] + '.\n')

	""" 2. Create a series of intermediate images that gradually step from the inital image to the final image, with just the color differing between images. """
	file_names_first_slow_option = [this_file_name for this_file_name in these_file_names if this_file_name.split('_')[1] == slow_change_options[0]]	# select all file names that have the first color option for the slow change

	for file_name_first_slow_option in file_names_first_slow_option:	# for each of those file names, grab the corresponding image with the other slow change option, and make a set of intermediate images (i.e. morphs between the two); For example, we will pair these images: Img01_Orange_yesWindow_noFlower.jpg and Img01_Yellow_yesWindow_noFlower.jpg and create a series of images gradually morphing between them

		image_data_first_slow_option = numpy.array(Image.open(os.path.join(jpg_path, file_name_first_slow_option)))	# import the image with this filename. At this point image_data_first_slow_option is some unusual object defined by the PIL module that the Image method belongs to (see imports above) and convert it to a numpy array: basically a matrix of RGB values

		file_name_second_slow_option = re.sub(slow_change_options[0], slow_change_options[1], file_name_first_slow_option)	# the iamge pairs that we morph between consist of identitical quick change states and opposite slow change color states. here, we can get the name of the ending image by simply swapping the color portion of the image name
		image_data_second_slow_option = numpy.array(Image.open(os.path.join(jpg_path, file_name_second_slow_option)))	# import the image and convert to numpy array

		for morph_step in range(number_of_morph_steps + 1):	# there will be one more frames than there are morph steps; a matter of definition I suppose

			image_data_morph = image_data_first_slow_option * (float(number_of_morph_steps - morph_step) / float(number_of_morph_steps)) + image_data_second_slow_option * (float(morph_step) / float(number_of_morph_steps))	# a weighted average of the two images' data gives us a morph. These are numpy arrays, which allow you to apply multiplication, addition, etc, to all elements all at once (which is what happens here). For python lists you'd have to do it per element.
			image_data_morph = image_data_morph.astype(numpy.uint8)	# the weighted average operation has changed the data type in the array from 8-bit int to float or something so we need to change it back before turning the morph data into an image.
			image_data_morph = Image.fromarray(image_data_morph, 'RGB')	# this turns it from a numpy array back into the PIL-related object type that Image.open() also gave us above. We can export that to an actual image file.
			
			output_filename = re.sub(slow_change_options[0], 'morph' + str(morph_step), file_name_first_slow_option)	# create the output filename for this morph
			image_data_morph.save(os.path.join(temp_path,output_filename))	# and export the data to a file with that name

	""" 3. Choose a "route" through the frames based on when you want the quick changes to happen. """
	quick_change_frames = []		# make a list of all the moments at which the quick changes happen
	for quick_change_index in range(num_quick_changes):
		new_change_moment_prop = ((float(quick_change_index) / float(num_quick_changes)) + (1. / float(num_quick_changes)) * float(1 - quick_change_time_section_proportion) / 2. + (1. / float(num_quick_changes)) * quick_change_time_section_proportion * numpy.random.rand())
		new_change_moment_frame = int(new_change_moment_prop*(number_of_morph_steps + 1))
		quick_change_frames.append(new_change_moment_frame)

	for curr_frame_index in range(number_of_morph_steps+1):		# walk through all the frames of our final sequence, and pick which version of that frame we want, based on when the quick changes happen; pick different quick change options (e.g. Window or Nowin) depending on whether the quick change in question has happened yet by the frame indicated by curr_frame_index

		# create a file_name for the current frame. it depends on frame index (morph) and number of changes. sets all to the first change option [0]. later we will update the change states depending on whether they have changed yet
		this_filename = filename_root + '_morph' + str(curr_frame_index)
		for one_change in range(len(quick_changes_in_name_order)):
			this_filename += '_' + quick_changes_in_name_order[one_change][0]
		this_filename += '.jpg'

		# for each of the quick changes, choose the appropriate version based on whether the change has occured
		for change_idx, quick_change_option_pair in enumerate(all_quick_change_options):
			# if the change has not happened yet, we do not need to do anything to the change component of this_filename because the name always starts with all of the initial states

			# if the change has started and is currently happening, create average morphs and save them out. update this_filename to reflect the "avg" state
			# because each quick change is designed to last one second, we create steps_per_second_video number of frames which allows the quick change to take place over the span of one second when converted to video
			if curr_frame_index >= quick_change_frames[change_idx] - int(quick_change_length_frames/2) and curr_frame_index < quick_change_frames[change_idx] + int(quick_change_length_frames / 2):	# while the change is happening

				imgA = this_filename	# imgA is the starting state image
				imgB = re.sub(quick_change_option_pair[0], quick_change_option_pair[1], this_filename)	# imgB is the ending state image
				image_quick_changeA = numpy.array(Image.open(os.path.join(temp_path, imgA)))
				image_quick_changeB = numpy.array(Image.open(os.path.join(temp_path, imgB)))
				count = quick_change_frames[change_idx] + (quick_change_length_frames / 2) - curr_frame_index	# this will help us keep track of the intermediate morphs that are created as a quick change happens. to make the quick changes last one second, as set in our global variables, we need to morph between the two states of the change quick_change_length_frames times

				# create weighted average of the two images; weight is determined by count
				quick_change_morph = (image_quick_changeA) * (float(change_step) * count) + (image_quick_changeB) * (1 - (float(change_step) * count)) 
				quick_change_morph = quick_change_morph.astype(numpy.uint8)	# change back to 8-bit
				quick_change_morph = Image.fromarray(quick_change_morph, 'RGB')	# this turns it from a numpy array back into the PIL-related object type that Image.open() also gave us above. We can export that to an actual image file.
				
				output_filename=re.sub(quick_change_option_pair[0], 'avg', imgA)	# create the output filename for this averaged morph
				quick_change_morph.save(os.path.join(temp_path, output_filename))	# save the new averaged morph
				
				this_filename = output_filename	# update this_filename to "choose" the avg version of this morph number

			# if the quick_change_frame for this change_idx has past, the change has occured. update the state of the current change to the changed state
			elif curr_frame_index >= quick_change_frames[change_idx] + int(quick_change_length_frames / 2):
				this_filename = re.sub(quick_change_option_pair[0], quick_change_option_pair[1], this_filename)

		# now that we have selected the version of the image that we want (this_filename), convert it to .tif, rename it to just contain the morph step, and save it in the morph_path
		image_data_this_frame = Image.open(os.path.join(temp_path, this_filename))	# get the image data into python again. The only reason to read it into python and then write it again, rather than simply moving and renaming the file we already have, is that we probably want to convert from .jpg to .tif, and this is one way of doing that. we want these images as tifs because they work better with ffmpeg for creating the morph; we also take this opportunity to adjust the dimensions of each image. image dimensions much each be divisible by 2 for ffmpeg to work so here, we adjust size of the image if needed
		width, height = image_data_this_frame.size
		width = width + 1 if width % 2 != 0 else width
		height = height + 1 if height % 2 != 0 else height
		image_data_this_frame = image_data_this_frame.resize((width, height))
		output_filename = filename_root + '_morph' + str(curr_frame_index) + '.tif'
		image_data_this_frame.save(os.path.join(morph_path, output_filename))

	""" 4. Prepare the input for ffmpeg and use ffmpeg to generate the video based on the selected frames. """
	# create a text file that lists in order the frames we want to add to the video. ffmpeg will read in the text file containing the list of filenames and string them together at the rate we defined above
	with open(os.path.join(morph_path,'makeVideo.txt'), "a+") as text_file:
		text_file.seek(0)	# move read cursor to the start of file.
		data = text_file.read(100)	# if file is not empty then append '\n'
		if len(data) > 0 :
			text_file.write("\n")
		
		# Append text at the end of file
		for frame_counter in range(no_change_in_frames):	# this adds no_change_in_frames number of lines to the text file so that ffmpeg will include no_change_in_seconds number of seconds of no changes at the start of the video using the initial frame
			text_file.write('file \'' + morph_path + '/' + filename_root + '_morph0.tif\'\n')
		text_file.write('file \'' + filename_root + '_morph%d.tif\'\n')	# adds each morph to the list in order according to the number after 'morph' in the file name
		for frame_counter in range(no_change_in_frames):	# this ensures no_change_seconds number of seconds of no changes at the end of the video using the final frame
			text_file.write('file \'' + morph_path + '/' + filename_root + '_morph' + str(number_of_morph_steps) + '.tif\'\n')
	
	image_size = numpy.array(image_data_this_frame).shape[:2]	# get image dimensions from most recent image. all dims are the same a this point after being resized, but we need to report the image size to ffmpeg
	video_file_name = filename_root + '_' + color.replace('_','') + '.mp4'	# name the final video Img#_ColorCombo.mp4

	# code adapted from http://hamelot.io/visualization/using-ffmpeg-to-convert-a-set-of-images-into-a-video/
	# these parameters can be changed as needed. more details about what these parameters are and how they affect the process can be found at the link
	my_shell_command = ffmpeg_path + ' -r ' + str(steps_per_second_video) + ' -f concat -safe 0 -i ' + os.path.join(morph_path,'makeVideo.txt') + ' -vcodec libx264 -crf 25 -pix_fmt yuv420p ' + os.path.join(output_path,video_file_name) + ' -video_size ' + str(image_size[0]) + 'x' + str(image_size[1]) + ' -frame_drop_threshold -3.1 -codec:v prores -qscale 2'		#this is a terminal command that one could type into the terminal to get the ffmpeg application to convert the .tif images into a .mp4 movie. Passing this command to 'subprocess.Popen' as shown below allows you to run the terminal command from python

	reply = subprocess.Popen(my_shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	print('Attempt to turn frames into a movie returned the following reply: ' + str(reply.communicate()[1]))	# this line will print what the shell command returns. It can be informative if the shell command doesn't work properly. simply comment this line out to avoid seeing the extra text.
	
	""" 5. Remove all temporary files from temp_path and morph_path and clear makeVideo.txt """
	# remove all temporary files from temp_path morph_path and clear makeVideo.txt
	for file_name in os.listdir(temp_path):
		os.remove(os.path.join(temp_path, file_name))
	for file_name in os.listdir(morph_path):	# for debugging or to preserve the selected frames that become the final video, comment out this loop
		if '.tif' in file_name:
			os.remove(os.path.join(morph_path, file_name))
	file = open(os.path.join(morph_path,'makeVideo.txt'), "r+")
	file.truncate(0)
	file.close()