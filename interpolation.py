
import torch
import argparse
import numpy as np
from helper import *
from config.GlobalVariables import *
from SynthesisNetwork import SynthesisNetwork
from DataLoader import DataLoader
import style

L = 256


def main(params):
    np.random.seed(0)
    torch.manual_seed(0)

    device = 'cpu'

    net = SynthesisNetwork(weight_dim=256, num_layers=3).to(device)

    if not torch.cuda.is_available():
        # net.load_state_dict(torch.load('./model_original/250000.pt', map_location=torch.device('cpu')))
        net.load_state_dict(torch.load('./model/248000.pt', map_location=torch.device('cpu'))["model_state_dict"])

    dl = DataLoader(num_writer=1, num_samples=10, divider=5.0, datadir='./data/writers')

    all_loaded_data = []

    for writer_id in params.writer_ids:
        loaded_data = dl.next_batch(TYPE='TRAIN', uid=writer_id, tids=[i for i in range(params.num_samples)])
        all_loaded_data.append(loaded_data)


    if params.task == "blend":
        if len(params.writer_weights) != len(params.writer_ids):
            raise ValueError("writer_ids must be same length as writer_weights")
        im = style.sample_blended_writers(params.writer_weights, params.target_word, net, all_loaded_data, device)
        im.convert("RGB").save(f'results/blend_{"+".join([str(i) for i in params.writer_ids])}.png')
    elif params.task == "grid":
        im = style.sample_character_grid(params.grid_letters, params.grid_size, net, all_loaded_data, device)
        im.convert("RGB").save(f'results/grid_{"+".join(params.grid_letters)}.png')
    elif params.task == "video":
        style.make_string_video(params.video_string, params.transition_time, net, all_loaded_data, device)
    else:
        print("Invalid task")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for generating samples with the handwriting synthesis model.')

    # parser.add_argument('--writer_id', type=int, default=80)
    parser.add_argument('--num_samples', type=int, default=10)
    parser.add_argument('--generating_default', type=int, default=0)

    parser.add_argument('--interpolate', type=str, default="writer", choices=["writer", "character"])
    parser.add_argument('--output', type=str, default="video", choices=["blend", "grid", "video"])

    # PARAMS FOR BOTH WRITER AND CHARACTER INTERPOLATION:
        # IF_BLEND
    parser.add_argument('--blend_weights', type=float, nargs="+", default=[0.5, 0.5])
        # IF GRID
    parser.add_argument('--grid_size', type=int, default=10)
        # IF VIDEO
    parser.add_argument('--video_time', type=int, default=10)

    # PARAMS IF WRITER INTERPOLATION:
    parser.add_argument('--target_word', type=str, default="hello")
    parser.add_argument('--writer_ids', type=int, nargs="+", default=[80, 120])
    
    # PARAMS IF CHARACTER INTERPOLATION:
        # IF BLEND
    parser.add_argument('--blend_chars', type=str, nargs="+", default = ["u", "g"])
        # IF GRID
    parser.add_argument('--grid_chars', type=str, nargs="+", default= ["x", "b", "u", "n"])
        # IF VIDEO
    parser.add_argument('--video_chars', type=str, default="abcdefghijklmnopqrstuvwxyz")

    
    main(parser.parse_args())
