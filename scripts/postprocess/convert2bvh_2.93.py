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

'''smplx_joint_names = {'root': 'root', 'bone_00': 'pelvis', 'bone_01': 'left_hip','right_hip',
                     'spine1','left_knee','right_knee',
                     'spine2','left_ankle','right_ankle',
                     'spine3', 'left_foot','right_foot','neck','left_collar','right_collar','head','left_shoulder','right_shoulder','left_elbow', 'right_elbow','left_wrist','right_wrist',
    'jaw','left_eye_smplhf','right_eye_smplhf','left_index1','left_index2','left_index3','left_middle1','left_middle2','left_middle3','left_pinky1','left_pinky2','left_pinky3','left_ring1','left_ring2','left_ring3','left_thumb1','left_thumb2','left_thumb3','right_index1','right_index2','right_index3','right_middle1','right_middle2','right_middle3','right_pinky1','right_pinky2','right_pinky3','right_ring1','right_ring2','right_ring3','right_thumb1','right_thumb2','right_thumb3'
}'''


def deg2rad(angle):
    return -np.pi * (angle + 90) / 180.


def init_scene(params):
    gender = params['gender']
    if (params['smplx']):
        try:
            # loads an smplx model using the addon
            bpy.data.window_managers["WinMan"].smplx_tool.smplx_gender = gender
            bpy.ops.scene.smplx_add_gender()

            obj_name = 'SMPLX-mesh-' + gender
            arm_obj_name = 'SMPLX-' + gender

        except AttributeError as e:
            print('')
            print(e)
            print('Install and enable smplx addon for blender')
            print('')
    else:
        # load fbx model
        bpy.ops.import_scene.fbx(filepath=join(params['smpl_data_folder'], 'basicModel_%s_lbs_10_207_0_v1.0.2.fbx' % gender[0]), global_scale=100)
        
        obj_name = '%s_avg' % gender[0]
        arm_obj_name = 'Armature'

    # delete the default stuff
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Cube'].select_set(True)
    bpy.data.objects['Camera'].select_set(True)
    bpy.data.objects['Light'].select_set(True)
    bpy.ops.object.delete()

    # clear existing animation data
    obj = bpy.data.objects[obj_name]
    obj.data.shape_keys.animation_data_clear()
    arm_obj = bpy.data.objects[arm_obj_name]
    arm_obj.animation_data_clear()

    return (obj, obj_name, arm_obj)


def Rodrigues(rotvec):
    theta = np.linalg.norm(rotvec)
    r = (rotvec/theta).reshape(3, 1) if theta > 0. else rotvec
    cost = np.cos(theta)
    mat = np.asarray([[0, -r[2], r[1]],
                      [r[2], 0, -r[0]],
                      [-r[1], r[0], 0]])
    return(cost*np.eye(3) + (1-cost)*r.dot(r.T) + np.sin(theta)*mat)


def rodrigues2bshapes(pose):
    print(len(pose))
    rod_rots = np.asarray(pose).reshape(24, 3)
    mat_rots = [Rodrigues(rod_rot) for rod_rot in rod_rots]
    bshapes = np.concatenate([(mat_rot - np.eye(3)).ravel() for mat_rot in mat_rots[1:]])
    return(mat_rots, bshapes)

# apply trans pose and shape to character
def apply_trans_pose_shape(trans, pose, shape, obj, arm_obj, obj_name, frame):
    # transform pose into rotation matrices (for pose) and pose blendshapes
    mrots, bsh = rodrigues2bshapes(pose)

    # set the location of the first bone to the translation parameter
    #arm_obj.pose.bones['pelvis'].location = trans
    #arm_obj.pose.bones['root'].location = trans
    #arm_obj.pose.bones['root'].keyframe_insert('location', frame=frame)

    # set the pose of each bone to the quaternion specified by pose
    for ibone, mrot in enumerate(mrots):
        print(ibone)
        continue
        bone = arm_obj.pose.bones[obj_name+'_'+part_match['bone_%02d' % ibone]]
        bone.rotation_quaternion = Matrix(mrot).to_quaternion()
        if frame is not None:
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            bone.keyframe_insert('location', frame=frame)

    quit()
    # apply pose blendshapes
    for ibshape, bshape in enumerate(bsh):
        obj.data.shape_keys.key_blocks['Pose%03d' % ibshape].value = bshape
        if frame is not None:
            obj.data.shape_keys.key_blocks['Pose%03d' % ibshape].keyframe_insert(
                'value', index=-1, frame=frame)

    # apply shape blendshapes
    for ibshape, shape_elem in enumerate(shape):
        obj.data.shape_keys.key_blocks['Shape%03d' % ibshape].value = shape_elem
        if frame is not None:
            obj.data.shape_keys.key_blocks['Shape%03d' % ibshape].keyframe_insert(
                'value', index=-1, frame=frame)



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
    print('Frames ', len(filenames))
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
    obj, obj_name, arm_obj = init_scene(params)

    # unblocking both the pose and the blendshape limits
    for k in obj.data.shape_keys.key_blocks.keys():
        bpy.data.shape_keys[0].key_blocks[k].slider_min = -10
        bpy.data.shape_keys[0].key_blocks[k].slider_max = 10

    motions = load_motions(params['path'])
    for pid, data in motions.items():

        arm_obj.animation_data_clear()

        # load smpl params:
        nFrames = data['poses'].shape[0]
        for frame in range(nFrames):
            trans = data['Th'][frame]
            shape = data['shapes'][0]
            pose = data['poses'][frame]

            apply_trans_pose_shape(Vector(trans), pose, shape, obj, arm_obj, obj_name, frame)
            bpy.context.view_layer.update()

        bpy.ops.export_anim.bvh(filepath=join(params['out'], '{}.bvh'.format(pid)), frame_start=0, frame_end=nFrames-1)
    return 0


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

