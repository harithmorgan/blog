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


refresh_index_page()

for files in sorted_txtfiles: 

    var_dict = grab_txtfile_variables(files)

    #generate blog page 
    if (not os.path.exists(var_dict['html_filename'])):
        generate_html_file(var_dict, 'prosetemplate.html')    
        print('new file generated')

    elif (var_dict['overwrite_permission']=='yes'):
        generate_html_file(var_dict,'prosetemplate.html')
        print('previous file overwritten: ' + str(files))
            
    else:   
        print('file already exists, will not overwrite: ' + str(files))


    #update home page to link to blog posts
    update_index_page(var_dict)
    print('\n')

