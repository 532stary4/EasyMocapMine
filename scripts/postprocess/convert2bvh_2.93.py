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
import os
import json
from mathutils import Matrix, Vector, Quaternion, Euler


part_match = {'root': 'root', 'bone_00': 'Pelvis', 'bone_01': 'L_Hip', 'bone_02': 'R_Hip',
              'bone_03': 'Spine1', 'bone_04': 'L_Knee', 'bone_05': 'R_Knee', 'bone_06': 'Spine2',
              'bone_07': 'L_Ankle', 'bone_08': 'R_Ankle', 'bone_09': 'Spine3', 'bone_10': 'L_Foot',
              'bone_11': 'R_Foot', 'bone_12': 'Neck', 'bone_13': 'L_Collar', 'bone_14': 'R_Collar',
              'bone_15': 'Head', 'bone_16': 'L_Shoulder', 'bone_17': 'R_Shoulder', 'bone_18': 'L_Elbow',
              'bone_19': 'R_Elbow', 'bone_20': 'L_Wrist', 'bone_21': 'R_Wrist', 'bone_22': 'L_Hand', 'bone_23': 'R_Hand'}


def deg2rad(angle):
    return -np.pi * (angle + 90) / 180.


def init_scene(params):
    if (params['smplx']):
        pass
    else:
        gender = params['gender']

        # load fbx model
        bpy.ops.import_scene.fbx(filepath=join(params['smpl_data_folder'], 'basicModel_%s_lbs_10_207_0_v1.0.2.fbx' % gender[0]), axis_forward='-Y', axis_up='-Z', global_scale=100)
        
        obj_name = '%s_avg' % gender[0]
        obj = bpy.data.objects[obj_name]

        # delete the default stuff
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['Cube'].select_set(True)
        bpy.data.objects['Camera'].select_set(True)
        bpy.data.objects['Light'].select_set(True)
        bpy.ops.object.delete()

        # clear existing animation data
        obj.data.shape_keys.animation_data_clear()
        arm_obj = bpy.data.objects['Armature']
        arm_obj.animation_data_clear()

    return (obj, obj_name, arm_obj)


def read_json(path):
    with open(path) as f:
        data = json.load(f)
    return data


def read_smpl(path):
    if os.path.exists(path):
        datas = read_json(path)
        outputs = []
        for data in datas:
            for key in ['Rh', 'Th', 'poses', 'shapes']:
                data[key] = np.array(data[key])
            outputs.append(data)

        return outputs
    else:
        print(path, ' not found!')
        quit()


def merge_params(param_list):
    output = {}
    for key in ['poses', 'shapes', 'Rh', 'Th', 'expression']:
        if key in param_list[0].keys():
            output[key] = np.vstack([v[key] for v in param_list])

    output['shapes'] = output['shapes'].mean(axis=0, keepdims=True)
    return output


def load_motions(datapath):
    from glob import glob
    filenames = sorted(glob(join(datapath, '*.json')))
    print(filenames)
    motions = {}
    for filename in filenames:
        infos = read_smpl(filename)
        for data in infos:
            pid = data['id']
            if pid not in motions.keys():
                motions[pid] = []
            motions[pid].append(data)

    for pid in motions.keys():
        motions[pid] = merge_params(motions[pid])
        motions[pid]['poses'][:, :3] = motions[pid]['Rh']
    return motions


def main(params):
    scene = bpy.data.scenes['Scene']

    obj, obj_name, arm_obj = init_scene(params)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # unblocking both the pose and the blendshape limits
    for k in obj.data.shape_keys.key_blocks.keys():
        bpy.data.shape_keys["Key"].key_blocks[k].slider_min = -10
        bpy.data.shape_keys["Key"].key_blocks[k].slider_max = 10

    bpy.context.view_layer.objects.active = arm_obj
    motions = load_motions(params['path'])

    quit()
    for pid, data in motions.items():

        # animation
        arm_obj.animation_data_clear()

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
            parser.add_argument('--smplx', action='store_true')
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