# -*- coding: utf-8 -*-
"""
Created on Sun May 10 11:44:44 2020

@author: Hesiris
"""

import os
import mutagen
DEBUG = False

def get_all_files(path,base,files = [],
                  extensions = ['mp3', 'flac',
                                'm4a', '.ogg'],
                  group_title = ''):
    """
    Parameters
    ----------
    path : str, path
        The path to be parsed
    base : str, path
        base path, in which the playlist will be saved
        this is removed from the results.
        E.g. if path == 'C:/Music/Artist' and
        base == 'C:/Music' the filenames in the
        return value will be Artist/Song.format
    files : list of str, optional
        The file list. Can be specified to
        include file names not in the folder. 
        The default is [].

    Returns
    -------
    files : str
        the list of files in the directory

    """
    #using .replace resuted in a '\\folder' type relative path, which was 
    #interpreted as Drive:\\folder
    relative = os.path.relpath(path,base)
    # All files and folders in path
    ff = os.listdir(path)
    
    #Folders are gathered and are recursively added after files
    folders = []
    if group_title != '':
        files.append('?#EXTGRP:' + group_title)
    
    for name in ff:
        #If name is a file, the extension is validated and appened to the list
        if os.path.isfile(os.path.join(path,name)):
            if os.path.splitext(name)[-1][1:].lower() in extensions:
                files.append(os.path.join(relative,name))
        else:
            #If name is a folder, it is saved for later processing.
            #Full path is added in the function call
            folders.append(name)
            
    for folder in folders:
        #The folder names will only have the name of the folder, without path,
        #therfore that needs to be attached. The base remains unchanged
        files = get_all_files(os.path.join(path,folder),
                              base,files,
                              group_title=folder)
        
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

def save_tracklist_to_file(tracks,input_folder,output_fn):
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
                    meta = mutagen.File(os.path.join(input_folder,fn))
                    #If no meta can be retrieved 0 is used as placeholder for length
                    length = int(meta.info.length) if meta is not None else 0
                    
                    #if the file name cannot be retrieved, the file name is 
                    #used instead (default value of title)
                    artist, title = get_artist_title(meta,
                            title = os.path.splitext(
                                        os.path.basename(fn))[0])
                    #The EXTINF field only has 2 fields, {} - {} is only a 
                    #convention. If the artist cannot be retrieved, it is skipped
                    if len(artist)>0:
                        g.write('#EXTINF:{},{} – {}\n'.format(
                            length,
                            artist,
                            title))
                    else:
                        g.write('#EXTINF:{},{}\n'.format(
                            length,
                            title))
                    g.write(fn)
                g.write('\n')

if __name__ == '__main__':
    # Create Playlist
    # Merge Playlists
    # Split Playlists
    # Insert into Playlist
    choice = int(input('Welcome to the playlist manipulator\n'
                       'Press a key:\n'
                       '1. Create a playlist from a folder\n'
                       '2. Merge several playlists\n'
                       '3. Split a playlist, if it has components\n'
                       '4. Insert songs from a folder into a playlist\n'))
    
    if choice == 1:
        path =input("Please specify the directory to parse. If none is "
                    "specified, the save file's path will be used\n")
        
        base = input("Please specify the start of the relative path.\n"
                     "If none is specified, the parse path will be used\n")
        
        output_fn = input("Please specify save filename.\n")
        
        if len(output_fn)<1:
            raise ValueError("The output path must be specified")
        if len(path)<1:
            path = os.path.dirname(path)
        if len(base)<1:
            base = path
            
        fns = get_all_files(path,base,
                 group_title = os.path.splitext(
                     os.path.basename(output_fn))[0])
        
        save_tracklist_to_file(fns,base,output_fn)
        
        groupcount = sum([1 if fn[:9]=='?#EXTGRP:' in fn else 0 for fn in fns])
        songcount = len(fns) - groupcount
        
        print('{} songs in {} groups have been saved to file'
                      .format(songcount,groupcount))
    elif choice == 2:
        fn = input("Enter the file name of the first playlist to be merged.\n"
                  "Pressing enter on an empty line will finish collecting the \n"
                  "Paths and prompt for the save file name\n")
        if fn[0]=="'" and fn[-1]=="'":
            fn = fn[1:-1]
        
        merged = open(fn, 'r', encoding='utf').readlines()
        
        while True:
            fn = input("Enter next file name:\n")
            if fn == '':
                break
            if fn[0]=="'" and fn[-1]=="'":
                fn = fn[1:-1]
            try:
                partial = open(fn, 'r', encoding='utf').readlines()
                if partial[1][:8] != '#EXTGRP:':
                    merged.append('#EXTGRP:{}\n'.format(os.path.splitext(
                                            os.path.basename(fn))[0]))
                merged += partial[1:]
            except Exception as e:
                print("Could not read from file: {}".format(e))
        
        fn_out = input("Enter output playlist filename:\n")
        open(fn_out,'w',encoding='utf-8').writelines(merged)
            
            
    elif choice == 3:
        print ("Not implemented")
        
    elif choice == 4:
        print ("Not implemented")
        