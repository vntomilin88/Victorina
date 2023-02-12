# -*- coding: utf-8 -*-
"""
Created on 2022.11.19
@author: vntom

Program that takes two folder names:
1: address of the folder with the original photos and the comments file in the main Pictures folder
2: address of the folder where the website is
And creates and HTML file for the website, as well as a folder with compressed images
"""

pathtomedia = '/Terra/Oblachko/Pictures/2021/Better late than never honemoon/7 - Venezia/2021_9_Venezia'
pathtowebsite = '/Terra/Oblachko/Website'
displaytitle = 'Venezia 2021'

# pathtomedia = '/Terra/Oblachko/Pictures/2021/Better late than never honemoon/6 - Milano/2021_9_Milano'
# pathtowebsite = '/Terra/Oblachko/Website'
# displaytitle = 'Milano 2021'

import os
import piexif # module that reads the exif information of the photo
import shutil
from math import sqrt
from PIL import Image, ImageOps

albumtitle = pathtomedia[pathtomedia.rfind('/')+1:] # searches for the last slash in the pathtomedia address which is the albumtitle, and since it contains the year, we use that as well
year = albumtitle[:albumtitle.find('_')]

''' First is the the check for Comments.txt in the folder, if there is no Comments.txt we create it'''
file_list = sorted(os.listdir(pathtomedia))
if 'Comments.txt' in file_list: #if Comments file is present we delete it from the file list for the media manipulation.
    print('Comments present')
    file_list.remove('Comments.txt')
    print(f'{len(file_list)} images found')
else: # else if Comments file does not exist, create the boilerplate version.
    print('No Comments, creating boiler plate')
    media_num = len(file_list) #since no comment file exist, all the remaining files are media
    text = 'Введение\n' #the 0th line of the comments file, the introduction before media text

    for i in range(1, media_num+1):
        text += f'{i}. \n'
    
    with open(f'{pathtomedia}/Comments.txt', mode='w') as comments:
        comments.write(text)
        print('Comments created')

'''Read the existing or created Comments file and save the text to a variable for future use in the html'''
with open(f'{pathtomedia}/Comments.txt', mode='r') as c:
    text = c.readlines() #text[0][:-1] - Introduction line before the media comments

'''Tryes to create website folder for the photos, if it exists moves on'''
try:
    os.makedirs(f'{pathtowebsite}/media/{year}/{albumtitle}')
except:
    pass

'''In this block we take the original media, delete metadata, shrink the filesize to ~500Kb each and save to the website media folder, as well as providing the adress for the html file'''
mediacode = '' #string that will store the html code corresponding to the photos and their comments
for mda in file_list:
    if mda[16:]=='mp4': #checks if the file is a video
        vdo = mda
        video_num = file_list.index(vdo)+1 #we take the number of the video in the file folder add 1 to it to make the new name of the photo
        video_adrs = f'/media/{year}/{albumtitle}/{str(video_num)}.mp4' 
        mediacode += f'''\t\t\t<tr><td><video width="1280" height="720" preload="auto" controls><source src='{video_adrs}' type="video/mp4"></video></td></tr>\n\t\t\t<tr><td>{text[video_num][:-1]}</td></tr>\n''' # text[video_num][:-1] takes the coresponding line from the comments file and removes the /n from the end
        if os.path.isfile(f'{pathtowebsite}/media/{year}/{albumtitle}/{str(video_num)}.mp4'):
            print(f'{str(video_num)}.mp4 already exists')
        else:
            print(f'Creating {pathtowebsite}/media/{year}/{albumtitle}/{str(video_num)}.mp4')
            shutil.copyfile(f'{pathtomedia}/{vdo}',f'{pathtowebsite}/media/{year}/{albumtitle}/{str(video_num)}.mp4')
    else:
        pht = mda
        photo_num = file_list.index(pht)+1 #we take the number of the photo in the file folder add 1 to it to make the new name of the photo
        photo_adrs = f'/media/{year}/{albumtitle}/{str(photo_num)}.jpg' 
        
        
        photo = Image.open(f'{pathtomedia}/{pht}')
        try:
            photo = ImageOps.exif_transpose(photo) # Images from some cameras would be rotated due to an orientation (img._getexif()[274]) mishandling in PIL, this fixes it (https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose)
        except:
            pass

        # original_exif_dict = piexif.load(photo.info['exif']) #complete dictionary exif of the original file; Keys: ['0th', 'Exif', 'GPS', 'Interop', '1st', 'thumbnail']
        exif_dict = {'Exif':{}}
        exif_dict['Exif'][42016] = f'{pht[::-1][::2]}' # exif_dict['Exif'][42016] - image unique ID; pht[::-1][::2] - we take the name of the file, reverse it and take every second character in the name to create a unique identifier
        exif_bytes = piexif.dump(exif_dict)

        w, h = photo.size
        if w*h > 1920000: #If the image is above 1.92 megapixels, shrink it down to that size, otherwise continue
            propotion = sqrt(w*h/1920000) #since image size is pixels squared, proportion is square root of it
            photo = photo.resize((int(w/propotion),int(h/propotion)))
        if h/w>1: #in order for the vertical photos to look good we have to add a width to the style atribute at 50%
            mediacode += f'''\t\t\t<tr><td><a href='{photo_adrs}'><img src='{photo_adrs}' style='width:50%'></a></td></tr>\n\t\t\t<tr><td>{text[photo_num][:-1]}</td></tr>\n''' # text[photo_num][:-1] takes the coresponding line from the comments file and removes the /n from the end
        else: #else the photos are horizontal and standard width is 90%
            mediacode += f'''\t\t\t<tr><td><a href='{photo_adrs}'><img src='{photo_adrs}'></a></td></tr>\n\t\t\t<tr><td>{text[photo_num][:-1]}</td></tr>\n''' # text[photo_num][:-1] takes the coresponding line from the comments file and removes the /n from the end
        
        '''Check to see if the modified photos have already been saved to the website folder through unique ID exif tag '''
        try:
            website_photo = Image.open(f'{pathtowebsite}/media/{year}/{albumtitle}/{str(photo_num)}.jpg') #opens the photo already in the folder
            website_photo_exif_dict = piexif.load(website_photo.info['exif']) #loads exif dictionary
            if str(website_photo_exif_dict['Exif'][42016])[2:-1]== f'{pht[::-1][::2]}': #checks if the existing image unique ID exif matches the newly created image
                print(f'Exif match for {pht}')
                continue
            else:
                photo.save(f'{pathtowebsite}/media/{year}/{albumtitle}/{str(photo_num)}.jpg', 'JPEG', exif=exif_bytes) #if the exif tag does not match, means photos have been changed, and we go ahead and replace
        except:
            photo.save(f'{pathtowebsite}/media/{year}/{albumtitle}/{str(photo_num)}.jpg', 'JPEG', exif=exif_bytes) #if the file does not exist at all we save as a new file with unique ID exif


with open(f'{pathtowebsite}/Albums/{year}/{albumtitle}.html', mode='w') as a:
    a.write(f'''<!DOCTYPE html>
<html>
	<head>
	<meta charset="utf-8"/>
		<title>{albumtitle}</title>'''
'''		
        <style>
		a:link
			{
				color: #AFD7E1;
				background-color: transparent;
				text-decoration: none;
			}
		a:visited
			{
				color: #AFD7E1;
				background-color: transparent;
				text-decoration: none;
			}
		a:hover
			{
				color: #D0D0D0;
				background-color: transparent;
				text-decoration: underline;
			}
		body
			{
				font-family: sans-serif;
				font-size: 1.5em;
				text-align: center;
				background-color: #2a2a2a;
			}
		table
			{
				background-color: #2a2a2a;
				width: 90%;
				padding: 20px;
			}
		th
			{
				font-size: 2.5em;
				color: #D0D0D0;
				background-color: #2a2a2a;
				padding: 10px;
			}
		img
			{
				width: 90%
			}
		td
			{
				color: #D0D0D0;
				padding: 2%;
				text-align: center;
			}
		</style>
	</head>
'''f'''
	<body>
		<table align="center">
            <tr><th scope="row">{displaytitle}</th></tr>
            <tr><td colspan="2" style="font-size: 1.5em; text-align: center">{text[0][:-1]}</td></tr>
            {mediacode}
		</table>
	</body>
</html>''')