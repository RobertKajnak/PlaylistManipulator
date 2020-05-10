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
    relative = path.replace(base,'')
    ff = os.listdir(path)
    
    folders = []
    if group_title != '':
        files.append('?#EXTGRP:' + group_title)
    
    for name in ff:
        if os.path.isfile(os.path.join(path,name)):
            if os.path.splitext(name)[-1][1:].lower() in extensions:
                files.append(os.path.join(relative,name))
        else:
            folders.append(name)
            
    for folder in folders:
        files = get_all_files(os.path.join(path,folder),
                              base,files,
                              group_title=folder)
        
    return files
        

def _rest_dict(d):
    try:
        for key,val in d.items():
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


if __name__ == '__main__':
    # Create Playlist
    # Merge Playlists
    # Split Playlists
    # Insert into Playlist
    choice = int(input('Welcome to the playlist manipulator\n'
                       'Press a key:\n'
                       '1. Create a playlist from a folder\n'
                       '2. Merge two playlists\n'
                       '3. Split a playlists, if it has components\n'
                       '4. Insert songs from a folder into a playlist\n'))
    
    if choice == 1:
        path =input("Please specify the directory to parse. If none is "
                    "specified, the save file's path will be used\n")
        #"P:\\アニメ"# 
        base = input("Please specify the start of the relative path.\n"
                     "If none is specified, the parse path will be used\n")
        #"P:\\"
        output_fn = input("Please specify save filename.\n")#"P:\\アニメ.m3u"
        
        if len(output_fn)<1:
            raise ValueError("The output path must be specified")
        if len(path)<1:
            path = os.path.dirname(path)
        if len(base)<1:
            base = path
        
        fns = get_all_files(path,base,
                 group_title = os.path.splitext(
                     os.path.basename(output_fn))[0])
        
        with open(output_fn,'w', encoding="utf-8") as g:
            g.write('#EXTM3U\n')
            for fn in fns:
                if fn[0]=='?':
                    g.write(fn[1:])
                else:
                    meta = mutagen.File(os.path.join(base,fn))
                    # meta = mutagen.mp3.MP3(os.path.join(base,fn))
                    # print(meta)
                    length = int(meta.info.length) if meta is not None else 0
                    artist, title = get_artist_title(meta,
                            title = os.path.splitext(
                                        os.path.basename(fn))[0])
                    
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
        #songcount = sum([1 if fn[:7]=='#EXTINF'  else 0 for fn in fns])
        groupcount = sum([1 if fn[:8]=='?#EXTGRP' in fn else 0 for fn in fns])
        songcount = len(fns) - groupcount
        print('{} songs in {} groups have been saved to file'
                      .format(songcount,groupcount))
    elif choice == 2:
        print ("not implemented")
        
    elif choice == 3:
        print ("Not implemented")
        
    elif choice == 4:
        print ("Not implemented")
        