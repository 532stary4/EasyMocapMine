'''
  @ Date: 2020-07-27 16:51:24
  @ Author: Qing Shuai
  @ LastEditors: 532stary4
  @ LastEditTime: 2021-10-15 21:54:03
  @ FilePath: /EasyMocapRelease/scripts/postprocess/convert2bvh_2.93.py
'''

import sys
import bpy
from os.path import join
import math
import numpy as np
from mathutils import Matrix, Vector, Quaternion, Euler

from scripts.postprocess.convert2bvh import init_scene

def deg2rad(angle):
    return -np.pi * (angle + 90) / 180.

part_match = {'root': 'root', 'bone_00': 'Pelvis', 'bone_01': 'L_Hip', 'bone_02': 'R_Hip',
              'bone_03': 'Spine1', 'bone_04': 'L_Knee', 'bone_05': 'R_Knee', 'bone_06': 'Spine2',
              'bone_07': 'L_Ankle', 'bone_08': 'R_Ankle', 'bone_09': 'Spine3', 'bone_10': 'L_Foot',
              'bone_11': 'R_Foot', 'bone_12': 'Neck', 'bone_13': 'L_Collar', 'bone_14': 'R_Collar',
              'bone_15': 'Head', 'bone_16': 'L_Shoulder', 'bone_17': 'R_Shoulder', 'bone_18': 'L_Elbow',
              'bone_19': 'R_Elbow', 'bone_20': 'L_Wrist', 'bone_21': 'R_Wrist', 'bone_22': 'L_Hand', 'bone_23': 'R_Hand'}


def init_scene(scene, params):
    gender = params['gender']
    angle = 0

    # load fbx model
    bpy.ops.import_scene.fbx(filepath=join(params['smpl_data_folder'], 'basicModel_%s_lbs_10_207_0_v1.0.2.fbx' % gender[0]), axis_forward='-Y', axis_up='-Z', global_scale=100)
    
    obj_name = '%s_avg' % gender[0]
    obj = bpy.data.objects[obj_name]

    # do i need it?
    #bpy.data.meshes[obj_name].use_auto_smooth = False # autosmooth creates artifacts

    # assign the existing spherical harmonics material
    #obj.active_material = bpy.data.materials['Material']

    # delete the default cube (which held the material)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Camera'].select_set(True)
    bpy.ops.object.delete()

    # set camera properties and initial position
    bpy.ops.object.select_all(action='DESELECT')
    cam_obj = bpy.data.objects['Camera']
    bpy.context.view_layer.objects.active = cam_obj

    th = deg2rad(angle)

    cam_obj.data.angle = math.radians(60)
    cam_obj.data.lens = 60
    cam_obj.data.clip_start = 0.1
    cam_obj.data.sensor_width = 32

    scene.view_layers[].use_pass_vector = True
    scene.view_layers[].use_pass_normal = True
    scene.view_layers[].use_pass_emit = True
    scene.view_layers[].use_pass_material_index = True

    # set render settings
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'

    # clear existing animation data
    obj.data.shape_keys.animation_data_clear()
    arm_obj = bpy.data.objects['Armature']
    arm_obj.animation_data_clear()

    return (obj, obj_name, arm_obj, cam_obj)

def main(params):
    scene = bpy.data.scenes['Scene']

    obj, obj_name, arm_obj, cam_obj = init_scene(scene, params)

    quit()
    deselect()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # unblocking both the pose and the blendshape limits
    # for loop

    bpy.context.view_layer.objects.active = arm_obj
    motions = load_smpl_params(params['path'])
    for pid, data in motions.items():

        # animation
        arm_obj.animation_data_clear()
        cam_obj.animation_data_clear()

        # load smpl params:








if __name__ == '__main__':
    try:
        import argparse
        if bpy.app.background:
            parser = argparse.ArgumentParser(
                description='Create keyframed animated skinned SMPL mesh from VIBE output')
            parser.add_argument('path', type=str,
                help='Input file or directory')
            parser.add_argument('--out', dest='out', type=str, required=True,
                help='Output file or directory')
            parser.add_argument('--smpl_data_folder', type=str,
                default='./data/smplx/SMPL_maya',
                help='Output file or directory')
            parser.add_argument('--gender', type=str,
                default='male')
            args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
            print(vars(args))
            main(vars(args))

    except SystemExit as ex:

        if ex.code is None:
            exit_status = 0
        else:
            exit_status = ex.code

        print('Exiting. Exit status: ' + str(exit_status))

        # Only exit to OS when we are not running in Blender GUI
        if bpy.app.background:
            sys.exit(exit_status)