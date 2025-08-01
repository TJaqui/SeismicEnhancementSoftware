import torch
from paths import resource_path

START_TRAIN_AT_IMG_SIZE = 128
DATASET = 'data/class1'
CHECKPOINT_GEN = resource_path("checkpoints/PGGAN.pth")
CHECKPOINT_CRITIC = "critic.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SAVE_MODEL = True
LOAD_MODEL = True
LEARNING_RATE = 1e-3
BATCH_SIZES = [25, 25, 25, 25, 25, 25, 25]
CHANNELS_IMG = 1
Z_DIM = 256
IN_CHANNELS = 256
CRITIC_ITERATIONS = 1
LAMBDA_GP = 10
PROGRESSIVE_EPOCHS = [8,16,20,100,350,550,30]
FIXED_NOISE = torch.randn(8, Z_DIM, 1, 1).to(DEVICE)
NUM_WORKERS = 4