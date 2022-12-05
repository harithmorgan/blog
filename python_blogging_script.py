import bs4
import os 
from datetime import datetime
import numpy


#///////////////////////    FUNCTIONS   ///////////////////////////
def grab_txtfile_variables(txtfile):
    var_dict = {} #create dictionary for variables
    var_dict['blog_content'] = str()
    filename = "blog_txtfiles\\" + txtfile
    info = open(filename, encoding='utf-8').readlines()
    
    is_blog_content = False
    while len(info) > 0:

        line = info.pop(0)
        line_contents = line.strip().split('=')
       
        if len(line_contents) > 0:
            if 'blog_content' in line_contents[0]:
                is_blog_content = True
            
            if (is_blog_content) and (']' in line_contents[0]):
                is_blog_content = False

        if ('blog_content' not in line_contents[0]):
            if is_blog_content:
                var_dict['blog_content'] += line_contents[0] + '<br>'
            elif len(line_contents) > 1:
                var_dict[line_contents[0].strip()] = line_contents[1].strip() 
    return var_dict

def generate_html_file(var_dict, template_file):
    # load the template file
    with open(template_file, 'rb') as html:
        page_code = str(bs4.BeautifulSoup(html,"html.parser").prettify())
        html.close()

    # replace appropriate sections from template
    for place_holder in var_dict.keys():
        page_code = page_code.replace(place_holder,var_dict[place_holder])

    # create and save new file
    with open(var_dict['html_filename'], "w", encoding = 'utf-8') as outf:
        outf.write(page_code)
        outf.close()

def add_prev_next_posts(var_dict, previous_var_dict, next_var_dict):
    # load current blog page
    with open(var_dict['html_filename'], 'rb') as html:
        page_code = bs4.BeautifulSoup(html,"html.parser")
        html.close()
    
    # print(page_code.prev_next_posts["style"]["visibility"])
    # pass
    page_code.prev_next_posts["style"] ="visibility: visible;"
    page_code = page_code.prettify()

    #add info for previous post
    page_code = page_code.replace("previous_","")
    for place_holder in previous_var_dict.keys():
        page_code = page_code.replace(place_holder,previous_var_dict[place_holder])
    
    #add infor for next post
    page_code = page_code.replace("next_","")
    for place_holder in next_var_dict.keys():
        page_code = page_code.replace(place_holder,next_var_dict[place_holder])


    #save updated blog file
    with open(var_dict['html_filename'], "w", encoding = 'utf-8') as outf:
        outf.write(page_code)
        outf.close()

def add_related_posts(tags_dict, html_file):
    ##create related posts section:

    var_dict = grab_txtfile_variables(html_file)
    file_to_edit = var_dict["html_filename"]
    # print(var_dict)
    related_posts_content =""
    for tag in var_dict["blog_tags"].split():
        # print(tag)
        for related_blog in tags_dict[tag]:
    
            with open("blogpost_tile_template.html", 'rb') as html:
                related_post_tile = str(bs4.BeautifulSoup(html,"html.parser").prettify())
                html.close()

            var_dict = grab_txtfile_variables(related_blog)
            for place_holder in var_dict.keys():
                related_post_tile = related_post_tile.replace(place_holder,var_dict[place_holder])
                related_post_tile = related_post_tile.replace("col-lg-4","col-lg-2")
                related_post_tile = related_post_tile.replace("col-md-6","col-md-3")
                related_post_tile = related_post_tile.replace("col-sm-6","col-sm-3")

            related_posts_content += related_post_tile    

    with open(file_to_edit, 'rb') as html:
        page_code = bs4.BeautifulSoup(html,"html.parser")
        html.close()

    page_code.related_posts.contents = []
    page_code.related_posts.extend(bs4.BeautifulSoup(related_posts_content,"html.parser"))
   
    # create and save new file
    with open(file_to_edit, "w", encoding = 'utf-8') as outf:
        outf.write(str(page_code.prettify()))
        outf.close()

    # print('\n')

def refresh_index_page():
    # grab the code from current index file
    with open('index.html', 'rb') as html:
        index_page_code = bs4.BeautifulSoup(html,"html.parser")
        html.close()

    index_page_code.blog_post_tiles.contents = []

    # create and save new file
    with open("index.html", "w", encoding = 'utf-8') as outf:
        outf.write(index_page_code.prettify())
        outf.close()

def update_index_page(var_dict):
    # load the template for new blog post tile
    with open('blogpost_tile_template.html', 'rb') as html:
        new_post_code = bs4.BeautifulSoup(html,"html.parser").prettify()
        html.close()

    # replace appropriate sections from template
    for place_holder in var_dict.keys():
        new_post_code = new_post_code.replace(place_holder,var_dict[place_holder])

    # grab the code from current index file
    with open('index.html', 'rb') as html:
        index_page_code = bs4.BeautifulSoup(html,"html.parser")
        html.close()

    #focus on blog posts, parse out invdiviual tiles
    current_posts = index_page_code.blog_post_tiles.prettify()
    temp = current_posts.split('<!-- ///////// -->')
    indv_tiles = [temp[i] + '<!-- ///////// -->' for i in range(len(temp)-1)] + [temp[-1]]
    # indv_tiles = [temp[i] + '<!-- ///////// -->' for i in range(len(temp))]

    #update blog tiles with overwrite permission
    for i in range(len(indv_tiles)):
        if (var_dict['html_filename'] in indv_tiles[i]) and (var_dict['overwrite_permission'] == 'yes'):
            indv_tiles[i] = new_post_code 
            print('tile updated')

    #finalize arrangement of tiles(appended newest to top)
    if (var_dict['html_filename']  not in current_posts):
        updated_posts = new_post_code + current_posts[60:-20]
        print("new blog tile added to index page")
    else:
        # print(indv_tiles[-2:-1])
        updated_posts = ''.join(indv_tiles)[60:-20]
        print("blog tile already exists")
        
    index_page_code.blog_post_tiles.contents = []
    index_page_code.blog_post_tiles.extend(bs4.BeautifulSoup(updated_posts,"html.parser"))
   
    # create and save new file
    with open("index.html", "w", encoding = 'utf-8') as outf:
        outf.write(index_page_code.prettify())
        outf.close()
    
#///////////////////////    MAIN CODE   ///////////////////////////////

currentdir = os.getcwd()
list_txtfiles = os.listdir(currentdir + "\\blog_txtfiles")

#sort list of files by date written
dates_written = {}
for files in list_txtfiles: 
    var_dict = grab_txtfile_variables(files)
    date_written = datetime.strptime(var_dict['blog_date'], '%B %d, %Y')
    dates_written[files] = date_written
sorted_txtfiles = sorted(list_txtfiles, key = lambda x: dates_written[x])

#clear index page of blog tiles
refresh_index_page()

#create blog pages and update index page
for ii in range(len(sorted_txtfiles)):

    ##define variable dictionaries
    if (ii == 0): previous_var_dict = {"blog_title": "Main Page", "html_filename": "index.html"}
    else: previous_var_dict = grab_txtfile_variables(sorted_txtfiles[ii-1])
    
    if (ii == len(sorted_txtfiles)-1): next_var_dict = {"blog_title": "Coming Soon", "html_filename": "index.html"}
    else: next_var_dict = grab_txtfile_variables(sorted_txtfiles[ii+1])
    
    var_dict = grab_txtfile_variables(sorted_txtfiles[ii])
    files = sorted_txtfiles[ii]

    ##generate blog page 
    if (not os.path.exists(var_dict['html_filename'])):
        generate_html_file(var_dict,'prosetemplate.html')
        add_prev_next_posts(var_dict, previous_var_dict, next_var_dict)    
        print('new file generated')

    elif (var_dict['overwrite_permission']=='yes'):
        generate_html_file(var_dict,'prosetemplate.html')
        add_prev_next_posts(var_dict, previous_var_dict, next_var_dict)
        print('previous file overwritten: ' + str(files))
            
    else:   
        print('file already exists, will not overwrite: ' + str(files))

    

    ##update home page to link to blog posts
    update_index_page(var_dict)
    print('\n')

#add related posts to each blog page(based on common tags)
tags_dict = {}
for files in list(reversed(sorted_txtfiles)): 
    var_dict = grab_txtfile_variables(files)
    #create dictionary that has files sorted by tags
    for tag in var_dict['blog_tags'].split():
        tags_dict.setdefault(tag,[]).append(files)

for files in sorted_txtfiles:
    add_related_posts(tags_dict, files)
