# -*- coding: utf-8 -*-
"""
Created on Wed May 13 12:55:46 2020

@author: Hesiris
"""

import os
from shutil import copy2

import unittest
import playlist_manipulator

class PlaylistTestCase(unittest.TestCase):
    # Test and gold standard paths
    testfilenames = ['tests/playlist_create_testcase_1.m3u',
                     'tests/playlist_create_testcase_2.m3u',
                     'tests/playlist_merge_testcase.m3u',
                    'tests/playlist_insert_testcase1.m3u',
                    'tests/playlist_insert_testcase2.m3u']
    
    goldfilenames = ['tests/playlist_create_gold_1.m3u',
                     'tests/playlist_create_gold_2.m3u',
                     'tests/playlists_merge_gold.m3u',
                     'tests/playlist_insert_gold1.m3u',
                     'tests/playlist_insert_gold2.m3u']
    
    testfolders = ['tests/split_results']
    
    def test_create(self):
        self.args.mode = 1
        self.args.path=[os.path.join('tests','music')]
        prefixes=['','music\\songs']
        
        #Test with and without prefix
        for i in range(2):
            self.args.output_fn=self.testfilenames[i]
            self.args.prefix = prefixes[i]
            
            f = open(self.goldfilenames[i],'r',encoding='utf-8')\
                        .readlines()
            playlist_manipulator.execute_main(True,self.args)
            g = open(self.testfilenames[i],'r',encoding='utf-8')\
                        .readlines()
            
            with self.subTest(i=i):
                self.assertEqual(f, g)
    
    def test_merge(self):
        self.args.mode = 2
        self.args.path = [self.goldfilenames[i] for i in [0,1,0]]
        self.args.output_fn = self.testfilenames[2]
        
        f = open(self.goldfilenames[2],'r',encoding='utf-8')\
            .readlines()
        playlist_manipulator.execute_main(True,self.args)
        g = open(self.testfilenames[2],'r',encoding='utf-8')\
                    .readlines()
        self.assertEqual(f,g)
    
    def tests_split(self):
        self.args.mode = 3
        self.args.path = [self.goldfilenames[0]]
        self.args.output_fn = self.testfolders[0]
        
        try:
            os.mkdir(self.args.output_fn)
        except:
            pass
        
        playlist_manipulator.execute_main(True,self.args)
        
        allfiles = os.listdir(self.args.output_fn)
        expected = ['Artist1.m3u','Album1.m3u','Album2.m3u','日本の歌手.m3u']
        
        # Check if all files are there, and no other files are there
        # listdir does not add . and ..
        self.assertTrue(len(allfiles)==4 and \
                        all([exp in allfiles for exp in expected]))
        
    
    def test_insert(self):
        self.args.mode = 4
        paths = [[os.path.join('tests','music','Artist1','Song5.mp3')],
                 [os.path.join('tests','music','Artist1')],
                 [os.path.join('tests','music','Artist1','Album1','Song1.mp3')]]
        self.args.prefix = 'Artist1\\Album1'
        
        
        for i in range(2):
            #A copy of the original needs to be made first to be inserted into
            copy2(self.goldfilenames[0],self.testfilenames[3+i])
            
            self.args.path = paths[i]
            self.args.output_fn = self.testfilenames[3+i]
            self.args.target_group = 1
            f = open(self.goldfilenames[3+i],'r',encoding='utf-8')\
                .readlines()
            #test insertion at the end
            playlist_manipulator.execute_main(True,self.args)
            
            #test insertion at the beginning
            self.args.path = paths[2]
            self.args.target_group = 0
            playlist_manipulator.execute_main(True,self.args)
            
            g = open(self.testfilenames[3+i],'r',encoding='utf-8')\
                        .readlines()
                    
        self.assertEqual(f,g)
        
        
    def setUp(self):
        args = type('', (), {})()
        self.args = args

    def tearDown(self):
        #delete created playlists
        # return
        for fn in self.testfilenames:
            if os.path.exists(fn):
                os.remove(fn)
                
        for fn in self.testfolders:
            if os.path.exists(fn):
                for fl in os.listdir(fn):
                    os.remove(os.path.join(fn,fl))
                os.rmdir(fn)
    

if __name__ == '__main__':
    unittest.main()