import numpy as np
from PIL import Image
from backend.app.inference.preprocess import preprocess

def test_grayscale_bilinear_resize_replicated_and_normalized():
    image=Image.new('RGB',(2,1))
    image.putdata([(0,0,0),(255,255,255)])
    tensor=preprocess(image)
    assert tensor.shape==(3,224,224)
    assert np.allclose(tensor[0]*0.229+0.485,tensor[1]*0.224+0.456,atol=1e-5)
    assert float(tensor[0].min()) < float(tensor[0].max())
    assert np.isfinite(tensor).all()

