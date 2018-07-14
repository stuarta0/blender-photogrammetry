from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty
from bpy.types import PropertyGroup


class PMVSPropertyGroup(PropertyGroup):
    dirpath = StringProperty(name='PMVS Data Directory', subtype='DIR_PATH', default='//pmvs')
    level = IntProperty(name='Level', default=1, min=0, description='When level is 0, original (full) resolution images are used. When level is 1, images are halved (or 4 times less pixels). And so on')
    csize = IntProperty(name='Cell Size', default=2, min=1, description='Controls the density of reconstructions. increasing the value of cell size leads to sparser reconstructions')
    threshold = FloatProperty(name='Threshold', default=0.7, min=0.15, description='A patch reconstruction is accepted as a success and kept, if its associcated photometric consistency measure is above this threshold. The software repeats three iterations of the reconstruction pipeline, and this threshold is relaxed (decreased) by 0.05 at the end of each iteration')
    wsize = IntProperty(name='Window Size', default=7, min=1, description='The software samples wsize x wsize pixel colors from each image to compute photometric consistency score.  Increasing the value leads to more stable reconstructions, but the program becomes slower')
    minImageNum = IntProperty(name='Min Image Num', default=3, min=2, description='Each 3D point must be visible in at least this many images to be reconstructed. If images are poor quality, increase this value')
    import_points = BoolProperty(name='Import point cloud after reconstruction', default=False)
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop(self, 'level')
        layout.prop(self, 'csize')
        layout.prop(self, 'threshold')
        layout.prop(self, 'wsize')
        layout.prop(self, 'minImageNum')
        layout.prop(self, 'import_points')
