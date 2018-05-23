import torch
import numpy as np
from PFNN import BaseNet, PFNN
from BVH import BVH
from hyperparams import *
from Dataset import BVHDataset

frames = 1000


def base_net_inference():
    bvh = BVH()
    bvh.load(bvh_path)
    net = BaseNet(num_of_frames*bvh.num_of_angles, bvh.num_of_angles).double()
    net.load_state_dict(torch.load('models/pfnn_params29.pkl'))
    init_x = torch.tensor(bvh.motion_angles[:num_of_frames]).view(-1)
    x = init_x
    motions = torch.zeros((frames, bvh.num_of_angles), requires_grad=False)
    # state = torch.tensor(bvh.motions[num_of_frames+1, 3:].reshape(-1))
    y = torch.tensor(bvh.motion_angles[num_of_frames].reshape(-1))
    # print(list(net.parameters()))
    # for p in net.parameters():
    #     print(p)
    # for k in net.state_dict():
    #     print(k)
    #     print(net.state_dict()[k])
    #     # xx.copy_(params)
    for i in range(frames):
        motions[i] = y
        x = torch.cat((x[bvh.num_of_angles:], y), 0)
        print(x.shape)
        y = net(torch.tensor(x).view(-1))

        # print(state)
    # print(motions.detach().numpy().shape)
    all_states = np.concatenate((np.zeros((frames, 3)),
                                 np.ones((frames, 3))*100,
                                 motions.detach().numpy()), axis=1)
    print(all_states.shape)
    bvh.save(output_path, all_states)


start_index = 196


def pfnn_inference():
    dataset = BVHDataset(base_dir + bvh_path)
    print(dataset.in_features, dataset.out_features)
    pfnn = PFNN(dataset.in_features, dataset.out_features).float()
    pfnn.load_state_dict(torch.load('models/pfnn_params90.pkl'))
    bvh = dataset.bvh
    init_state = dataset.bvh.motions[start_index, :num_of_root_infos]
    init_angles = bvh.motion_angles[start_index]
    phase = 0
    # print(len(dataset[0]))
    trajectory = dataset[start_index][0][0][:num_of_root_infos *
                                            trajectory_length]
    # print(len(trajectory))
    motions = np.zeros((frames, bvh.num_of_angles+num_of_root_infos))
    angles = init_angles
    state = init_state
    # print(angles.shape)
    # print(trajectory)
    fake_trajectory = np.zeros((trajectory_length, num_of_root_infos))
    fake_trajectory[:, 1] = 0.2*delta_scale
    for i in range(frames):
        print('i:  ', i)
        x = torch.cat(
            (torch.tensor(fake_trajectory, dtype=torch.float32)
             .view(1, num_of_root_infos*trajectory_length),
             torch.tensor(angles, dtype=torch.float32).view(1, 90)), dim=1)
        y = pfnn(x, phase)
        # print(y.shape)
        trajectory = y[:, :trajectory_length*num_of_root_infos]
        phase += y[0, trajectory_length*num_of_root_infos]/phase_scale
        phase = phase.detach()
        angles = y[:, trajectory_length*num_of_root_infos+1:]
        # print(y.shape)
        # print(angles.shape)
        delta_state = trajectory[0, :num_of_root_infos]
        delta_state[0] /= delta_scale
        delta_state[2] /= delta_scale
        state += delta_state.detach()
        # print(state.reshape(1, num_of_root_infos).shape)
        # print(angles.detach().numpy().shape)
        motions[i] = np.concatenate(
            (state.reshape(1, num_of_root_infos), angles.detach().numpy()),
            axis=1)
    bvh.save(output_path, motions)
    smoothed_motions = np.concatenate(
        (np.zeros((frames, num_of_root_infos)),
         motions[:, num_of_root_infos:]),
        axis=1)
    bvh.save("smooth_"+output_path, smoothed_motions)


if __name__ == '__main__':
    pfnn_inference()
