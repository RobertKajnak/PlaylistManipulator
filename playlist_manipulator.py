# -*- coding: utf-8 -*-
"""
Created on Sun May 10 11:44:44 2020

@author: Hesiris
"""

import os
import re
from sys import argv
import argparse

import mutagen
    
DEBUG = False
EXTENSIONS = ['mp3', 'flac', 'm4a', '.ogg']

def get_all_files(path,prefix='',files = [],
                  extensions = ['mp3', 'flac',
                                'm4a', '.ogg'],
                  group_title = ''):
    """
    Parameters
    ----------
    path : str, path
        The path to be parsed
    base : str, path
        a prefix that is attached to the beginning of the filenames
        E.g. if path == 'C:/Music/Artist' and
        and the music will be stored later or on an other device
        under Music/Rock/
        return value will be Music/Rock/Song.format
    files : list of str, optional
        The file list. Can be specified to
        include file names not in the folder. 
        The default is [].

    Returns
    -------
    files : str
        the list of files in the directory

    """
    
    # All files and folders in path
    ff = os.listdir(path)
    
    if files == []:
        files = []
    
    #Folders are gathered and are recursively added after files
    folders = []
    if group_title != '':
        files.append('?#EXTGRP:' + group_title)
    
    for name in ff:
        #If name is a file, the extension is validated and appened to the list
        if os.path.isfile(os.path.join(path,name)):
            if os.path.splitext(name)[-1][1:].lower() in extensions:
                files.append(os.path.join(prefix,name))
        else:
            #If name is a folder, it is saved for later processing.
            #Full path is added in the function call
            folders.append(name)
            
    for folder in folders:
        #The folder names will only have the name of the folder, without path,
        #therfore that needs to be attached. The base remains unchanged
        files = get_all_files(os.path.join(path,folder),
                              os.path.join(prefix,folder),files,
                              group_title=folder,
                              extensions=extensions)
        
    return files
        

def _rest_dict(d):
    """
    Used for debugging. Prints the fields of a dictionary d, if the .items()
    is available. Otherwise prints the provided object

    Parameters
    ----------
    d : object, preferably dict
        An object containig metadata.

    Returns
    -------
    None.

    """
    try:
        for key,val in d.items():
            #covr is the cover art of songs, i.e. long base 64 image
            if key == 'covr':
                continue
            if isinstance(key, list):
                print(key[0][:20],' : ',val[:20][0])
            else:
                print(key[:20],' : ',val[:20])
    except:
        print(d)

def get_artist_title(meta, artist = '', title = ''):
    """
    Attempts to retrieve the artist and title from meta info
    These can be set as default values, in case the 
    information cannot be retreived

    Parameters
    ----------
    meta : dict
        meta dictionary from mutagen
    artist : string, optional
        fallback artist. The default is ''.
    title : string, optional
        fallback title. The default is ''.

    Returns
    -------
    artist : string
    title : string

    """
    #empirical analysis
    if meta is not None:
        unknown = False
        try:
            artist =  ', '.join(meta['artist'])
        except:
            try:
                artist =  ', '.join(meta['albumartist'])
            except:
                try:
                    artist = ', '.join(meta['©ART'])
                except:
                    try:
                        artist =  ', '.join(meta['TPE1'].text)
                    except:
                        unknown = True
            
        try:
            title =  ', '.join(meta['title'])
        except:
            try:
                title = ', '.join(meta['©nam'])
            except:
                try:
                    title =  ', '.join(meta['TIT2'].text)
                except:
                    unknown = True
                    
        if unknown and DEBUG:
            print('Unknown metadata:')
            _rest_dict(meta)
    
    return artist, title

def get_EXTINF(filename):
    meta = mutagen.File(filename)
    #If no meta can be retrieved 0 is used as placeholder for length
    length = int(meta.info.length) if meta is not None else 0
    
    #if the file name cannot be retrieved, the file name is 
    #used instead (default value of title)
    artist, title = get_artist_title(meta,
            title = os.path.splitext(
                        os.path.basename(filename))[0])
    #The EXTINF field only has 2 fields, {} - {} is only a 
    #convention. If the artist cannot be retrieved, it is skipped
    if len(artist)>0:
        return '#EXTINF:{},{} – {}\n'.format(
                                            length,
                                            artist,
                                            title)
    else:
        return '#EXTINF:{},{}\n'.format(
                                        length,
                                        title)

def save_tracklist_to_file(tracks,input_folder,prefix,output_fn):
    """
    Save a list of filenames and ? marked meta commands to the specified files,
    adding any necessary headers and extracting the meta information for the
    files

    Parameters
    ----------
    tracks : str
        A list of filenames.
    input_folder: str
        The parent input folder
    output_fn : str
        the file to save to.

    Returns
    -------
    None.

    """
    with open(output_fn,'w', encoding="utf-8") as g:
            #File header
            g.write('#EXTM3U\n') 
            for fn in tracks:
                #? lines mark commands. These are printed as-is
                if fn[0]=='?':
                    g.write(fn[1:])
                else:
                    if prefix=='':
                        true_path = os.path.join(input_folder,fn) 
                    else:
                        true_path = fn.replace(prefix,input_folder)
                    
                    g.write(get_EXTINF(true_path))
                    g.write(fn)
                g.write('\n')

def split_merged_playlist(merged):
    """
    Split a merged playlist into separate files. #EXTM3U and #EXTGRP: markers
    are used to determine splits. Empty groups are discarded

    Parameters
    ----------
    merged : list of strings
        a list containing the contents of a playlist file

    Returns
    -------
    split : dict
        keys are the name of the groups,
    groupcount : int
        number of non-emtyp groups
    unnamed_group_tag: str
        The prefix that denotes the separation of the sections

    """

    unnamed_group_tag = '__UNNAMED_GROUP_123?x_'    
    groupcount = 0
    split = {}

    for line in merged:
        if line[:8] == '#EXTGRP:' or line[:7] == '#EXTM3U':
            split_sublist = []
            groupcount += 1
            if line[:8] == '#EXTGRP:':
                split[line[8:]] = split_sublist
            #Unnamed groups are marked with a name that is unlikely to be used
            elif line[:7] == '#EXTM3U':
                split[unnamed_group_tag + str(groupcount)] =  split_sublist
        else:
            split_sublist.append(line)
    
    #Remove empty groups
    to_remove = []
    for key,val in split.items():
        if val == []:
            to_remove.append(key)
            groupcount -= 1
    for key in to_remove:
        split.pop(key)
    
    return split, groupcount, unnamed_group_tag

def reconstruct_merged_playlist(split,unnamed_group_tag):
    merged = ['#EXTM3U\n']
    for key, val in split.items():
        if key[:len(unnamed_group_tag)] == unnamed_group_tag:
            merged.append('#EXTM3U')
        else:
            merged.append('#EXTGRP:{}'.format(key))
        for line in val:
            merged.append(line)
    return merged

def sanitize_fn(fn):
    """ Sanitizes Filename. Removes beginning and trailing quotes"""
    if (fn[0]=="'" and fn[-1]=="'") or (fn[0]=='"' and fn[-1]=='"'):
        return fn[1:-1]
    return fn
        

def input_fn(prompt):
    """ Assumes input is a Filename. Removes beginning and trailing quotes"""
    ip = input(prompt)
    if len(ip)<1:
        return ip
    else:
        return sanitize_fn(ip)

def str_smaller_win(str1,str2):
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key)]
    return alphanum_key(str1)<alphanum_key(str2)

def execute_main(console_mode, args = None):
    CONSOLE_MODE = console_mode
    if CONSOLE_MODE:
        choice = args.mode
    else:
        choice = int(input('Welcome to the playlist manipulator!\n'
                           'Hint: The program can also be run via command line '
                           'parameter for repeated tasks. Start the program with '
                           'the --help parameter for details'
                            'Press a key:\n' + mode_tooltip))
    
    # Create
    if choice == 1:
        if CONSOLE_MODE:
            path=args.path[0]; prefix=args.prefix; output_fn=args.output_fn
            
        else:
            path =input_fn("Please specify the directory to parse. If none is "
                        "specified, the save file's path will be used\n")
            
            prefix = input_fn("Please specify the path prefix to be attached "
                              "before the filenames, e.g. C;/Music is parsed "
                              "but the paths should have Music at the "
                              "beginning, set prefix=Music")
            
            output_fn = input_fn("Please specify save filename.\n")
        
        if len(output_fn)<1:
            raise ValueError("The output path must be specified")
        if len(path)<1:
            path = os.path.dirname(path)
        
        fns = get_all_files(path,prefix,
                 group_title = os.path.splitext(
                     os.path.basename(output_fn))[0],
                 extensions= EXTENSIONS)
        save_tracklist_to_file(fns,path,prefix,output_fn)
        
        groupcount = sum([1 if fn[:9]=='?#EXTGRP:' in fn else 0 for fn in fns])
        songcount = len(fns) - groupcount
        
        print('{} songs in {} groups have been saved to file'
                      .format(songcount,groupcount))
    
    # Merge
    elif choice == 2:
        if CONSOLE_MODE:
            fns = args.path
            fn = fns[0]
            fn_idx = 1
        else:
            fn = input_fn("Enter the file name of the first playlist to be "
                          "merged.\n Pressing enter on an empty line will "
                          "finish collecting the paths and prompt "
                          "for the save file name\n")
        
        merged = open(fn, 'r', encoding='utf').readlines()
        
        while True:
            if CONSOLE_MODE:
                if fn_idx>= len(fns):
                    break
                fn = fns[fn_idx]
                fn_idx +=1
            else:
                fn = input_fn("Enter next file name:\n")
                if fn == '':
                    break

            try:
                partial = open(fn, 'r', encoding='utf').readlines()
                if partial[1][:8] != '#EXTGRP:':
                    merged.append('#EXTGRP:{}\n'.format(os.path.splitext(
                                            os.path.basename(fn))[0]))
                merged += partial[1:]
            except Exception as e:
                print("Could not read from file: {}".format(e))
        
        if CONSOLE_MODE:
            fn_out = args.output_fn
        else:
            fn_out = input_fn("Enter output playlist filename:\n")
        open(fn_out,'w',encoding='utf-8').writelines(merged)
           
        print('Playlist succesfully saved')
    # Split
    elif choice == 3:
        if CONSOLE_MODE:
            fn = args.path[0]
            output_dir = args.output_fn
        else:
            fn = input_fn("Enter the filename of the playlist to split:\n")
            output_dir = input_fn('{} groups have been found. Type in a folder to output the '
                  'playlists to\n'.format(groupcount))
        
        merged = open(fn, 'r', encoding='utf-8').readlines()
        split, groupcount, unnamed_group_tag = split_merged_playlist(merged)
        
        subcount = 1
        for sublist_name, sublist_elements in split.items():
            if sublist_name[:len(unnamed_group_tag)] \
                            == unnamed_group_tag:
                #Save unnamed groups with a more friendly name
                out_filename = 'Group {}'.format(subcount)
                subcount += 1
            else:
                out_filename = sublist_name.rstrip()
            
            out_filename = os.path.join(output_dir,out_filename+'.m3u')    
            # Warn if file exists
            if os.path.exists(out_filename):
                if CONSOLE_MODE:
                    if not args.overwrite:
                        continue
                else:
                    answer = input("File <<{}>> already exists. Overwrite? (y/n)\n"
                                   .format(out_filename))
                    if len(answer)<1 or answer[0].lower() != 'y':
                        continue
                
            # Add header and output contents. Group is removed and is in filename
            with open(out_filename,'w', encoding='utf-8') as out_file:
                out_file.write('#EXTM3U\n')
                out_file.writelines(sublist_elements)
                
        print('Files Saved')
        
    elif choice == 4:
        if CONSOLE_MODE:
            fn_to_append = args.path[0]
        else:
            fn_to_append = input_fn("Enter which file or files in folder to "
                                    "insert. "
                                    "The folder is not parsed recursively.\n")

        if os.path.exists(fn_to_append) and os.path.isfile(fn_to_append):
            fn_list = [fn_to_append]
        elif os.path.exists(fn_to_append) and os.path.isdir(fn_to_append):
            fn_list = os.listdir(fn_to_append)
            fn_list = [os.path.join(fn_to_append,f_s) for f_s in fn_list]
        else:
            raise SystemExit("Invalid file specified")
            
        if CONSOLE_MODE:
            fn_prefix = args.prefix
            fn_to_mod = args.output_fn
        else:
            fn_prefix = input_fn("Enter any prefix to add to file paths, "
                                 "or leave blank\n")
    
            fn_to_mod = input_fn("Enter playlist to insert into:\n")

        merged = open(fn_to_mod, 'r', encoding='utf-8').readlines()
        split, groupcount, unnamed_group_tag = split_merged_playlist(merged)
        

        if groupcount>1:
            if not CONSOLE_MODE:
                print("There are {} groups in the selected file. "
                  "Please select which group to add to:".format(groupcount))
            idx_to_group = {}
            for idx,group in enumerate(split.keys()):
                idx_to_group[idx] = group
                if not CONSOLE_MODE:
                    if group[:len(unnamed_group_tag)] == unnamed_group_tag:
                        print('{}. Unnamed group {}'.format(idx, 
                                            group[len(unnamed_group_tag):]
                                            .rstrip()))
                    else:
                        print('{}. {}'.format(idx,group.rstrip()))
                
            try:
                if CONSOLE_MODE:
                    idx = args.target_group
                else:
                    idx = int(input())
            except:
                raise SystemExit("Invalid number specified")
        else:
            print('There is only a single group in the file. Inserting')
            idx = 0
            #Creates a dictionary with a single entry that is the first group
            idx_to_group = {0:list(split.values())[0]}
        
        inserted_songs = []
        if idx in idx_to_group:
            target_group = split[idx_to_group[idx]]
            for f in fn_list:
                if os.path.splitext(f)[-1][1:].lower() in EXTENSIONS:
                    f_basename = os.path.basename(f)
                    for i,v in enumerate(target_group):
                        if v[:4] != '#EXT' and \
                        str_smaller_win(f_basename,os.path.basename(v)):
                            break;
                    else:
                        i+=2
                    target_group.insert(i-1,os.path.join(fn_prefix,
                                                    os.path.basename(f))+'\n')
                    target_group.insert(i-1,get_EXTINF(f))
                    inserted_songs.append(os.path.basename(f))
                    
            merged_new = reconstruct_merged_playlist(split, unnamed_group_tag)
            
            open(fn_to_mod,'w',encoding='utf-8').writelines(merged_new)
            print("{} songs have been inserted into the playlist:"
                                  .format(len(inserted_songs)))
            for song in inserted_songs:
                print(song)
            
        else:
            raise SystemExit("Invalid number specified")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Welcome to the playlist "
                    "manipulator, command line parameter edition. \nTo use the"
                    "interactive menu, start the command without any "
                    "parameters. \nUse this program to create an m3u playlist "
                    "from a folder, with groupings. \nIt can also merge and "
                    "split lists, or insert a new song into it. ",
                    formatter_class=argparse.RawTextHelpFormatter)
    
    mode_tooltip = "1. Create a playlist from a folder\n"\
                    "2. Merge several playlists\n"\
                    "3. Split a playlist, if it has components\n"\
                    "4. Insert songs from a folder into a playlist\n"
                
    parser.add_argument('-mode',
                    type = int,
                    help = mode_tooltip+'\n')
        
    parser.add_argument('-path',
                        type = str,
                        nargs='*',
                        help = 'By mode:\n'
                        '1: Folder containing songs\n'
                        '2: Paths separated by whitespaces to the playlists\n'
                        '3: Path to the playlist\n'
                        '4: The song to be inserted or folder containing the '
                        'songs to be inserted. \n'
                        'It is not parsed recursively\n\n')

    parser.add_argument('-output_fn',
                        type = str,
                        help = 'The file (1,2,4) or folder (3) where the '
                        'result will be output\n\n')
        
    parser.add_argument('-prefix',
                        type = str,
                        default = '',
                        help = 'Applies to modes 1 and 4 only\n'
                        'A prefix to be applied to the output files. \n'
                        'E.g. if the directory contains song Lala.mp3, '
                        'adding the prefix "Music" \nwill insert the song as '
                        'Music/Lala.mp3 into the playlist\n\n')
    
    parser.add_argument('--overwrite',
                         action = 'store_true',
                         help='Only applies to 3\n'
                         'If specified, existing files in the output '
                         'directory \nwill be overwritten; they are skipped '
                         'otherwise')
    
    parser.add_argument('-target_group', 
                        type=int,
                        default=0,
                        help = "Applies to mode 4 only\n"
                        "The group in which the seletcted songs will be "
                        "inserted into. \nCounting starts from 0")
    
    args = parser.parse_args()
    
    CONSOLE_MODE = True if len(argv)>1 else False
    
    execute_main(CONSOLE_MODE,args)
            
        
        
        
        
        