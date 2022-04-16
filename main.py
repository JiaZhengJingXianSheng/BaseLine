# -*- coding: utf-8 -*-
'''
@Time    : 2022/4/16 20:08
@Author  : LYZ
@FileName: main.py
@Software: PyCharm
'''
import Unet
import os
import rawpy
import numpy as np
import torch
from torch import nn

noisy_data_path = "dataset/noisy/"
origin_data_path = "dataset/ground_truth/"
NoisyFiles = os.listdir(noisy_data_path)
OriginFiles = os.listdir(origin_data_path)
NoisyFiles_len = len(NoisyFiles)
device = "cuda:0"
lr = 0.001
loss = nn.L1Loss()
epochs = 50


def read_image(input_path):
    raw = rawpy.imread(input_path)
    raw_data = raw.raw_image_visible
    height = raw_data.shape[0]
    width = raw_data.shape[1]

    raw_data_expand = np.expand_dims(raw_data, axis=2)
    raw_data_expand_c = np.concatenate((raw_data_expand[0:height:2, 0:width:2, :],
                                        raw_data_expand[0:height:2, 1:width:2, :],
                                        raw_data_expand[1:height:2, 0:width:2, :],
                                        raw_data_expand[1:height:2, 1:width:2, :]), axis=2)
    return raw_data_expand_c, height, width


def normalization(input_data, black_level, white_level):
    output_data = (input_data.astype(float) - black_level) / (white_level - black_level)
    return output_data


def pre(input_path):
    raw_data_expand_c, height, width = read_image(input_path)
    raw_data_expand_c_normal = normalization(raw_data_expand_c, black_level=1024, white_level=16383)
    raw_data_expand_c_normal = torch.from_numpy(np.transpose(
        raw_data_expand_c_normal.reshape(-1, height // 2, width // 2, 4), (0, 3, 1, 2))).float()
    return raw_data_expand_c_normal


if __name__ == "__main__":
    net = Unet.Unet()
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    net.to(device)

    net.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for i in range(NoisyFiles_len):
            X = pre(input_path=noisy_data_path + str(i) + "_noise.dng")
            Y = pre(input_path=origin_data_path + str(i) + "_gt.dng")
            X, Y = X.to(device), Y.to(device)
            optimizer.zero_grad()

            Y_HAT = net(X)
            l = loss(Y_HAT, Y)
            l.backward()
            optimizer.step()

            running_loss += l.item()
            print("Epoch{}\tloss {}".format(epoch,running_loss/NoisyFiles_len),end="")

        print()
        torch.save(net.state_dict(), 'models/BaseLine-' + str(epoch) + '.pth')