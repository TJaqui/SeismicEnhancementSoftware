import math
import torch
import numpy as np
from sporco import array,plot,util
from models.Attention_unet import AttU_Net
from tqdm import tqdm
import segyio
from segyio import TraceField
from pathlib import Path
import os
from paths import resource_path
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

def seismicEnhancement(data,shape,step=16, progress_callback=None):
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
    model_path = resource_path("checkpoints/att_u_fine.pt")
    model.load_state_dict(torch.load(model_path, weights_only=False, map_location=device))
    data_loader = torch.utils.data.DataLoader(data, batch_size=5)
    denoised_tensor_list = []
    total = len(data_loader)

    total_batches = len(data_loader)
    for i, batch in enumerate(tqdm(data_loader, desc="Enhancing")):
        with torch.no_grad():
            denoised_batch = model(batch.to(device).float())
            denoised_tensor_list.append(denoised_batch.cpu())

        if progress_callback:
            percent = int((i + 1) / total * 100)
            progress_callback(percent, f"Enhancing... {percent}%")

    recov_blcks = torch.cat(denoised_tensor_list, dim=0)

    
    del denoised_tensor_list
    print(recov_blcks.shape)
    Urec  = recov_blcks.squeeze().permute(1,2,0).cpu().numpy()
    Urec = Urec.reshape(np.prod(blksz), -1)
    imgd_median = array.combine_blocks(Urec.reshape(blksz + (-1,)), shape, stpsz, np.median)
    return imgd_median

def seismicEnhancement3D(data,shape,step=16, progress_callback=None):
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
    ruta_nueva = os.path.join(os.getcwd(), "checkpoints_runtime", "att_u_fine_new.pt")
    ruta_preentrenada = resource_path("checkpoints/att_u_fine.pt")

    if os.path.exists(ruta_nueva):
        model.load_state_dict(torch.load(ruta_nueva, weights_only=False, map_location=device))
    else:
        model.load_state_dict(torch.load(ruta_preentrenada, weights_only=False, map_location=device))

    data_loader = torch.utils.data.DataLoader(data, batch_size=5)
    denoised_tensor_list = []
    total = len(data_loader)

    total_batches = len(data_loader)
    for i, batch in enumerate(tqdm(data_loader, desc="Enhancing")):
        with torch.no_grad():
            denoised_batch = model(batch.to(device).float())
            denoised_tensor_list.append(denoised_batch.cpu())

        if progress_callback:
            percent = int((i + 1) / total * 100)
            progress_callback(percent, f"Enhancing... {percent}%")

    recov_blcks = torch.cat(denoised_tensor_list, dim=0)

    del denoised_tensor_list
    print(recov_blcks.shape)
    Urec  = recov_blcks.squeeze().permute(1,2,0).cpu().numpy()
    Urec = Urec.reshape(np.prod(blksz), -1)
    imgd_median = array.combine_blocks(Urec.reshape(blksz + (-1,)), shape, stpsz, np.median)
    return imgd_median

def save2dData(data, template_path, dstpath, dmin, dmax):
    denorm_enhanced=data
    template_file = Path(template_path)

    with segyio.open(str(template_file), 'r', ignore_geometry=True) as src:
        if denorm_enhanced.shape != src.trace.raw[:].shape:
            raise ValueError(f"Shape mismatch: data shape {denorm_enhanced.shape} vs trace shape {src.trace.raw[:].shape}")

        spec = segyio.spec()
        spec.format = src.format
        spec.samples = src.samples
        spec.tracecount = src.tracecount

        with segyio.create(str(dstpath), spec) as dst:
            dst.text[0] = src.text[0]
            dst.bin = src.bin
            dst.header = src.header
            dst.trace.raw[:] = denorm_enhanced

def denorm_0_1_to_range(x, orig_min, orig_max):
    """
    Undo a 0‑to‑1 normalization.

    Parameters
    ----------
    x : np.ndarray | torch.Tensor
        Data that was previously scaled to the [0, 1] interval.
    orig_min : float or array‑like
        The minimum value(s) in the *original* data distribution.
        Can be a scalar or per‑channel/feature array (broadcastable to `x`).
    orig_max : float or array‑like
        The maximum value(s) in the *original* data distribution.
        Must be broadcastable to `x`.

    Returns
    -------
    denorm : same type as `x`
        Data rescaled back to the original range.
    """
    if orig_max is None or orig_min is None:
        raise ValueError("Both `orig_min` and `orig_max` must be provided.")
    scale = (orig_max - orig_min)
    return x * scale + orig_min
def save3dData(data, template_path, dstpath, dmin, dmax):
    denorm_enhanced = denorm_enhanced.astype(np.float32).T
    
    template_file = Path(template_path)
    print(f"Saving 3D data to {template_file}")
    with segyio.open(str(template_file), 'r') as src:

  
        inlines  = np.asarray(src.ilines)
        xlines   = np.asarray(src.xlines)
       
       
        spec = segyio.spec()
        spec.format     = src.format
        spec.samples    = src.samples
        spec.ilines     = inlines
        spec.xlines     = xlines


        with segyio.create(str(dstpath), spec) as dst:
            dst.text[0] = src.text[0]
            dst.bin     = src.bin  # keeps sample interval, etc.

           
            for i, il in enumerate(inlines):
                
                #print(f"Saving inline { dst.iline[il].shape}")
                index = il-inlines[0] 
                
                

                dst.iline[il] = denorm_enhanced[index].T
                    # Set trace headers for each trace in the inline
                for j, xl in enumerate(xlines):
                    trace_index = i * len(xlines) + j
                    dst.header[trace_index][TraceField.INLINE_3D] = il
                    dst.header[trace_index][TraceField.CROSSLINE_3D] = xl
            

            dst.flush()

