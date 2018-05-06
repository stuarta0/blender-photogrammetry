import os


def load(self, data, dirpath):
    """
    Takes the structure calculated from parsing the input and writes to the bundler file structure
    """
    cameras = data['cameras']
    trackers = data['trackers']

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    # write the image list file that corresponds with the camera index in bundle.out
    with open(os.path.join(dirpath, 'list.txt'), 'w+') as f:
        f.writelines(['{}\n'.format(camera['filename']) for id, camera in cameras.items()])

    # now write the bundle file
    sift = 0
    with open(os.path.join(dirpath, 'bundle.out'), 'w+') as f:
        f.write('# Bundle file v0.3\n')
        f.write('{} {}\n'.format(len(cameras.items()), len(trackers.items())))
        for camera in cameras.values():
            f.write('{f} {k[0]} {k[1]}\n'.format(**camera))
            f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['R'][0]))
            f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['R'][1]))
            f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['R'][2]))
            f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['t']))
        
        # now write the points and corresponding matching cameras
        for tid, track in trackers.items():
            f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=track))
            f.write('255 255 255\n')  # TODO: RGB of point
            # calculate view list
            visible_in = {}
            for cid, camera in cameras.items():
                if tid in camera['trackers']:
                    visible_in[cid] = camera['trackers'][tid]  # visible_in[camera 4]: (x, y)
            f.write('{count}'.format(count=len(visible_in.items())))
            for cid, co in visible_in.items():
                # The pixel positions are floating point numbers in a coordinate system where the origin is the center of the image, 
                # the x-axis increases to the right, and the y-axis increases towards the top of the image. Thus, (-w/2, -h/2) is 
                # the lower-left corner of the image, and (w/2, h/2) is the top-right corner (where w and h are the width and height of the image).
                # http://www.cs.cornell.edu/~snavely/bundler/bundler-v0.4-manual.html
                f.write(' {idx} {sift} {co[0]} {co[1]}'.format(
                    idx=cid,
                    sift=sift,
                    co=co,))
                sift += 1
            f.write('\n')
