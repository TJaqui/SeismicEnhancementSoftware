import math
import torch
import numpy as np
from sporco import array,plot,util
from models.Attention_unet import AttU_Net
from tqdm import tqdm

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def mirror_padding(image, top_padding, bottom_padding, left_padding, right_padding):
    h, w = image.shape
    new_h = h + top_padding + bottom_padding
    new_w = w + left_padding + right_padding
    padded_image = np.zeros((new_h, new_w), dtype=image.dtype)
    
    padded_image[top_padding:top_padding + h, left_padding:left_padding + w] = image
    
    if top_padding > 0:
        padded_image[:top_padding, left_padding:left_padding + w] = image[:top_padding][::-1]
    
    if bottom_padding > 0:
        padded_image[top_padding + h:, left_padding:left_padding + w] = image[-bottom_padding:][::-1]
    
    if left_padding > 0:
        padded_image[top_padding:top_padding + h, :left_padding] = image[:, :left_padding][:, ::-1]
    
    if right_padding > 0:
        padded_image[top_padding:top_padding + h, left_padding + w:] = image[:, -right_padding:][:, ::-1]
    
    if top_padding > 0 and left_padding > 0:
        padded_image[:top_padding, :left_padding] = image[:top_padding, :left_padding][::-1, ::-1]
    
    if top_padding > 0 and right_padding > 0:
        padded_image[:top_padding, left_padding + w:] = image[:top_padding, -right_padding:][::-1, ::-1]
    
    if bottom_padding > 0 and left_padding > 0:
        padded_image[top_padding + h:, :left_padding] = image[-bottom_padding:, :left_padding][::-1, ::-1]
    
    if bottom_padding > 0 and right_padding > 0:
        padded_image[top_padding + h:, left_padding + w:] = image[-bottom_padding:, -right_padding:][::-1, ::-1]
    
    return padded_image

def padding(img):
    padd_img = img
    if (img.shape[0] % 128 != 0):
        pad = math.ceil(img.shape[0]/128)*128 - img.shape[0]
        if pad%2==0:
            top = int(pad/2)
            bot = int(pad/2)
        else:
            top = math.ceil(pad/2)
            bot = math.floor(pad/2)
        padd_img = mirror_padding(img,top,bot,0,0)
    if (img.shape[1] % 128 != 0):
        pad = math.ceil(img.shape[1]/128)*128 - img.shape[1]
        if pad%2==0:
            lf =int(pad/2)
            rt = int(pad/2)
        else:
            lf = math.ceil(pad/2)
            rt = math.floor(pad/2)
        padd_img = mirror_padding(padd_img,0,0,lf,rt)
    return padd_img, top, bot, lf, rt

def patchDivision(data, step=16):
    singleffid = data.copy()
    blksz = (128,128)
    stpsz = (step,step)
    blcks_corrupt = array.extract_blocks(singleffid, blksz, stpsz)
    subblcks_corrupt = blcks_corrupt.transpose(2,0,1)
    subblcks_corrupt = torch.from_numpy(subblcks_corrupt).unsqueeze(1)
    return subblcks_corrupt

def seismicEnhancement(data,shape,step=16):
    blksz = (128,128)
    stpsz = (step,step)
    model = AttU_Net(img_ch=1,output_ch=1).to(device)
    model.eval()
    model.load_state_dict(torch.load('checkpoints/att_u_fine.pt', weights_only=False))
    data_loader = torch.utils.data.DataLoader(data, batch_size=40)
    denoised_tensor_list = []

    for batch in tqdm(data_loader):
        with torch.no_grad():
            denoised_batch = model(batch.to(device).float())
            denoised_tensor_list.append(denoised_batch.cpu())
    recov_blcks = torch.cat(denoised_tensor_list, dim=0)
    
    del denoised_tensor_list
    print(recov_blcks.shape)
    Urec  = recov_blcks.squeeze().permute(1,2,0).cpu().numpy()
    Urec = Urec.reshape(np.prod(blksz), -1)
    #start = timeit.default_timer()
    imgd_median = array.combine_blocks(Urec.reshape(blksz + (-1,)), shape, stpsz, np.median)
    #print("creating image from patching, time is:",
    #            timeit.default_timer() - start)
    return imgd_median

def save2dData(data):

    pass
