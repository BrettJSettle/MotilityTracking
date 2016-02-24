# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 17:35:15 2016

@author: kyle
"""

import struct
import numpy as np

class BinaryReaderEOFException(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return 'Not enough bytes in file to satisfy read request'

class BinaryReader:
    # Map well-known type names into struct format characters.
    typeNames = {
        'int8'   :'b',
        'uint8'  :'B',
        'int16'  :'h',
        'uint16' :'H',
        'int32'  :'i',
        'uint32' :'I',
        'int64'  :'q',
        'uint64' :'Q',
        'float'  :'f',
        'double' :'d',
        'char'   :'s',
        'single' :'f'}

    def __init__(self, filename):
        self.filename=filename
        self.file = open(filename, 'rb')

    def seek(self, *args):
        return self.file.seek(*args)

    def tell(self, *args):
        return self.file.tell()

    def read_bytes(self, i):
        return self.file.read(i)
        
    def read(self, typeName):
        typeFormat = BinaryReader.typeNames[typeName.lower()]
        typeSize = struct.calcsize(typeFormat)
        value = self.file.read(typeSize)
        if typeSize != len(value):
            raise BinaryReaderEOFException
        a =  struct.unpack(typeFormat, value)[0]
        return a

    def close(self):
        self.file.close()

def i3DataType():
    #x, y, xc, yc in pixels.
    #z and zc in nanometer
    return np.dtype([('x', np.float32),   # original x location
                    ('y', np.float32),   # original y location
                    ('xc', np.float32),  # drift corrected x location
                    ('yc', np.float32),  # drift corrected y location
                    ('h', np.float32),   # fit height
                    ('a', np.float32),   # fit area
                    ('w', np.float32),   # fit width
                    ('phi', np.float32), # fit angle (for unconstrained elliptical gaussian)
                    ('ax', np.float32),  # peak aspect ratio
                    ('bg', np.float32),  # fit background
                    ('i', np.float32),   # sum - baseline for pixels included in the peak
                    ('c', np.int32),     # peak category ([0..9] for STORM images)
                    ('fi', np.int32),    # fit iterations
                    ('fr', np.int32),    # frame
                    ('tl', np.int32),    # track length
                    ('lk', np.int32),    # link (id of the next molecule in the trace)
                    ('z', np.float32),   # original z coordinate
                    ('zc', np.float32)]) # drift corrected z coordinate
                    
def i3_to_dict(i3data):
    d=dict()
    keys=i3data.dtype.fields.keys()
    for key in keys:
        d[key]=i3data[key][0]
    return d
    
def bin2mat(infile):
    '''
    import file of tracks as list of dicts with track info.
    
    Insight files are organized into a header and a number of molecule blocks
    
    header
    
            |  version           (string) M425
            |  number of frames  (int32)  number of frames in the original movie
            |  status            (int32)  identified = 2, stormed = 6, traced =3, tracked = 4
            
    molecule blocks
    
            |  number of molecules in block (int32)
            |  molecule info   (72 bytes)  i3DataType
            
            |  number of molecules in block (int32)
            |  molecule info   (72 bytes)  i3DataType
            
            .
            .
            .
            
            |  number of molecules in block (int32)
            |  molecule info   (72 bytes)  i3DataType
            
    
    Sometimes there is only one molecule block, sometimes there is one block for each frame. 
    
    The second configuration is how insight3 exports data.  Suppose your movie 
    has 1000 frames.  There will be 1001 molecule blocks.  The first block will
    contain the first molecule of every track.  Each of these molecules will 
    have two parameters that are required to find the next molecule of each 
    track: fr (frame number) and lk (id of the next molecule).  If we are 
    looking at the first molecule in the first block, and its frame number
    equals 7 and its link equals 2, then to find the next molecule in the track 
    is the 2nd molecule in the 7th molecule block.  
    
    
    
    
    '''
    if not infile.endswith('.bin'):
        raise Exception('Not a bin file')
    

    fid = BinaryReader(infile) # % file id or file identifier
    fid.seek(0, 2) # 
    file_length = fid.tell()
    fid.seek(0, 0)

    # read header
    version = "".join([str(fid.read('char')) for i in range(4)]) # *char % M425
    nFrames = fid.read('int32') # *int32 ;% number of frames. real frames.
    status = fid.read('int32') # *int32 ;% identified = 2, stormed = 6, traced =3, tracked = 4
    
    #nmol = fid.read('int32')  # number of molecules in the file
    header_length = fid.tell()
    
    sizeofminfo=4*len(np.zeros(1, dtype = i3DataType()).dtype.names)     # 72 bytes per minfo
    nmols=[]
    #fid.seek(int(sizeofminfo*nmols[-1]), 1)
    datas=[]
    while fid.tell()<file_length:
        nmol_in_block=fid.read('int32')
        nmols.append(nmol_in_block)
        data = np.fromfile(fid.file, dtype=i3DataType(), count=nmol_in_block)
        datas.append(data)
    fid.close()
    
    
        
    if nmols[0]==np.sum(nmols): # this means molecule lists in 1, 2, ... frames do not exist.  All the localizations are in one big block in memory
        data=np.hstack(datas)
        links=data['lk']
        tracks=[[i] for i in np.arange(len(links))]
        for p0, p1 in enumerate(links):
            if p1 != -1:
                merged=tracks[p0]+tracks[p1]
                for p in merged:
                    tracks[p]=merged
                    
        unique_tracks=np.unique(tracks)
        MList = []
        for track in unique_tracks:
            if len(track)>2:
                mol=dict()
                mol['x']         = data[track]['x']
                mol['y']         = data[track]['y']
                mol['frame']    = data[track]['fr']
                mol['xmean']     = np.mean(mol['x'])
                mol['ymean']     = np.mean(mol['y'])
                mol['selfframe'] = data[track]['fr']
                MList.append(mol)
    else:
        MList=[]
        for index in np.arange(nmols[0]):
            mol=datas[0][index]
            track=[]
            #mol=i3_to_dict(data)
            track.append(mol)
            fr=mol['fr']
            lk=mol['lk']
            while lk != -1:
                next_pt=datas[fr][lk]
                track.append(next_pt)
                fr=next_pt['fr']
                lk=next_pt['lk']
            track=np.hstack(track)
            
            mol=dict()
            mol['x']         = track['x']
            mol['y']         = track['y']
            mol['frame']    = track['fr']
            mol['xmean']     = np.mean(mol['x'])
            mol['ymean']     = np.mean(mol['y'])
            mol['selfframe'] = track['fr']
            MList.append(mol)

    
    print("Loaded %s molecules".format(len(MList)))
    return MList
    
if __name__=='__main__':
    infile=r'C:\Users\kyle\Desktop\test_insight.bin'
    MList=bin2mat(infile)
    
    
    
    
    