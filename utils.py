import math
import torch
import numpy as np
from sporco import array,plot,util
from models.Attention_unet import AttU_Net
from tqdm import tqdm

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def mirror_padding(image, top_padding, bottom_padding, left_padding, right_padding):
    """
    It applies mirror padding to a given 2D array. 
    It extends the image by adding rows and columns around its borders using a mirror reflection of the image's edge pixels.

    Parameters
    ----------
    image: ndarrat
        A 2D array representing the input image whose pixels are to be padded.
    top_padding: int
        An integer specifying the number of rows to be added to the top of the image by mirroring the top edge.
    bottom_padding: int
        An integer specifying the number of rows to be added to the bottom of the image by mirroring the bottom edge.
    left_padding: int
        An integer specifying the number of columns to be added to the left of the image by mirroring the left edge.
    right_padding: int
        An integer specifying the number of columns to be added to the right of the image by mirroring the right edge.

    Return
    -------
    padded_image : ndarray
        An array that includes the original image centered within a border of mirror-padded pixels, 
        having dimensions increased by the specified padding on all sides.
    """
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
    """
    It extends the image by adding rows and columns around its borders using a mirror reflection 
    of the image's edge pixels.

    Parameters
    ----------
    img : ndarray
        A 2D array representing the input image whose dimensions are to be adjusted to the nearest 
        multiple of 128 through mirror padding.

    Return
    ------
    padd_img : ndarray
        The mirror-padded image with height and width adjusted to the nearest multiple of 128.
    top : int
        Number of rows added to the top of the image.
    bot : int
        Number of rows added to the bottom of the image.
    lf : int
        Number of columns added to the left of the image.
    rt : int
        Number of columns added to the right of the image.
    """
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
    """
    It divides a 2D array into overlapping patches using a sliding window approach.
    The function extracts 128x128 blocks from the data with a specified step size,
    transposes the block dimensions, and converts the result into a PyTorch tensor with an added channel dimension.

    Parameters
    ----------
    data : ndarray
        A 2D array representing the input image or data from which patches are to be extracted.
    step : int
        An integer specifying the step size for the sliding window when extracting patches. 
        By default this parameter is set to 16.

    Return
    ------
    subblcks_corrupt : torch.Tensor
        A PyTorch tensor containing the extracted patches. The patches are unsqueezed to include a channel dimension.
    """
    singleffid = data.copy()
    blksz = (128,128)
    stpsz = (step,step)
    blcks_corrupt = array.extract_blocks(singleffid, blksz, stpsz)
    subblcks_corrupt = blcks_corrupt.transpose(2,0,1)
    subblcks_corrupt = torch.from_numpy(subblcks_corrupt).unsqueeze(1)
    return subblcks_corrupt

def seismicEnhancement(data,shape,step=16):
    """
    It performs seismic data enhancement using a pre-trained model.
    The function processes the input data by dividing it into patches, passing each patch through the model 
    for denoising/enhancement, and then concatenates the enhanced patches.

    Parameters
    ----------
    data : dataset-like
        The input data containing seismic images or signals to be enhanced. This data is expected to be compatible 
        with PyTorch's DataLoader.
    shape : tuple
        A tuple specifying the target shape of the enhanced seismic data.
    step : int, optional
        An integer specifying the step size for patch extraction, which determines the overlap between patches.
        By default this parameter is set to 16.

    Return
    ------
    recov_blcks : torch.Tensor
        A PyTorch tensor containing the enhanced seismic blocks obtained by concatenating the model's output from all batches.
    """
    blksz = (128,128)
    stpsz = (step,step)
    model = AttU_Net(img_ch=1,output_ch=1).to(device)
    model.eval()
    model.load_state_dict(torch.load('checkpoints/att_u_fine.pt', weights_only=False,map_location=torch.device("cpu")))
    data_loader = torch.utils.data.DataLoader(data, batch_size=5)
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
