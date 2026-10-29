from io import BytesIO
import numpy as np
from PIL import Image
import pytest
from backend.app.inference.registry import MODELS
from backend.app.inference.predict import gradcam

MODEL='D'
pytestmark=pytest.mark.skipif(not MODELS[MODEL][0].exists(),reason='Converted experiment D weights are required.')

def test_gradcam_size_range_and_finding_specificity():
    image=Image.fromarray(np.random.default_rng(17).integers(0,256,(180,240),dtype=np.uint8))
    maps=[]
    for label in ['Effusion','Pneumonia']:
        result=Image.open(BytesIO(gradcam(image,MODEL,label))).convert('RGB')
        arr=np.asarray(result)
        assert result.size==image.size
        assert arr.min()>=0 and arr.max()<=255
        assert arr.max()>0
        maps.append(arr)
    assert not np.array_equal(maps[0],maps[1])

def test_gradcam_can_restore_original_upload_dimensions():
    model_input=Image.fromarray(np.random.default_rng(8).integers(0,256,(224,224),dtype=np.uint8))
    result=Image.open(BytesIO(gradcam(model_input,MODEL,'Effusion',output_size=(320,280))))
    assert result.size==(320,280)
