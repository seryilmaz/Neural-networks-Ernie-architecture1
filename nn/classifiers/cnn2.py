import numpy as np,h5py 

from nn.layers import *
from nn.fast_layers import *
from nn.layer_utils import *
from nn.layer_utils import conv_sigmoid_pool_forward


class ThreeLayerConvNet(object):
  """
  A three-layer convolutional network with the following architecture:
  
  conv - relu - 2x2 max pool - affine - relu - affine - softmax
  
  The network operates on minibatches of data that have shape (N, C, H, W)
  consisting of N images, each with height H and width W and with C input
  channels.
  """
  
  def __init__(self, input_dim=(3, 32, 32), num_filters=32, filter_size=7,
               hidden_dim=100, num_classes=10, weight_scale=1e-3, reg=0.0,
               dtype=np.float32):
    """
    Initialize a new network.
    
    Inputs:
    - input_dim: Tuple (C, H, W) giving size of input data
    - num_filters: Number of filters to use in the convolutional layer
    - filter_size: Size of filters to use in the convolutional layer
    - hidden_dim: Number of units to use in the fully-connected hidden layer
    - num_classes: Number of scores to produce from the final affine layer.
    - weight_scale: Scalar giving standard deviation for random initialization
      of weights.
    - reg: Scalar giving L2 regularization strength
    - dtype: numpy datatype to use for computation.
    """
    self.params = {}
    self.reg = reg
    self.dtype = dtype

    C, H, W = input_dim
    self.params['W1'] = weight_scale * np.random.randn(num_filters, C, filter_size, filter_size)
    self.params['b1'] = np.zeros([num_filters])
    self.params['W2'] = weight_scale * np.random.randn(num_filters*H*W/4, hidden_dim)
    self.params['b2'] = np.zeros([hidden_dim])
    self.params['W3'] = weight_scale * np.random.randn(hidden_dim, num_classes)
    self.params['b3'] = np.zeros([num_classes])


    for k, v in self.params.iteritems():
      self.params[k] = v.astype(dtype)
     
 
  def loss(self, X, y=None):
    """
    Evaluate loss and gradient for the three-layer convolutional network.
    
    Input / output: Same API as TwoLayerNet in fc_net.py.
    """
    W1, b1 = self.params['W1'], self.params['b1']
    W2, b2 = self.params['W2'], self.params['b2']
    W3, b3 = self.params['W3'], self.params['b3']
    
    # pass conv_param to the forward pass for the convolutional layer
    filter_size = W1.shape[2]
    conv_param = {'stride': 1, 'pad': (filter_size - 1) / 2}

    # pass pool_param to the forward pass for the max-pooling layer
    pool_param = {'pool_height': 2, 'pool_width': 2, 'stride': 2}

    scores = None

    out, conv_cache = conv_relu_pool_forward(X,W1,b1,conv_param,pool_param)
    out, relu_cache = affine_relu_forward(out, W2, b2)
    scores, affine_cache = affine_forward(out, W3, b3)

    
    if y is None:
      return scores
    
    loss, grads = 0, {}

    loss, dscores = softmax_loss(scores, y)
    loss += 0.5 * self.reg * (np.sum(W1*W1) + np.sum(W2*W2) + np.sum(W3*W3))
    dx, dW3, db3 = affine_backward(dscores, affine_cache)
    dx, dW2, db2 = affine_relu_backward(dx, relu_cache)
    dx, dW1, db1 = conv_relu_pool_backward(dx, conv_cache)
    dW1 += self.reg * W1
    dW2 += self.reg * W2
    dW3 += self.reg * W3
    grads.update({'W1':dW1, 'b1':db1, 'W2':dW2, 'b2':db2, 'W3':dW3, 'b3':db3})

    return loss, grads
  
  

class ConvNet2(object):
    
    
  def __init__(self, input_dim=(3, 32, 32), num_filters=[32, 64, 64], filter_size=3,
               num_classes=10, weight_scale=[1e-3, 1e-3, 1e-3, 1e-3], reg=0.0,
               dtype=np.float32):
    """
    Initialize a new network.
    
    Inputs:
    - input_dim: Tuple (C, H, W) giving size of input data
    - num_filters: Number of filters to use in the convolutional layer
    - filter_size: Size of filters to use in the convolutional layer
    - hidden_dim: Number of units to use in the fully-connected hidden layer
    - num_classes: Number of scores to produce from the final affine layer.
    - weight_scale: Scalar giving standard deviation for random initialization
      of weights.
    - reg: Scalar giving L2 regularization strength
    - dtype: numpy datatype to use for computation.
    """
    self.params = {}
    self.reg = reg
    self.dtype = dtype
  
    C, H, W = input_dim
    self.params['W1'] = weight_scale[0] * np.random.randn(num_filters[0], C, filter_size, filter_size)
    self.params['b1'] = np.zeros([num_filters[0]])
    self.params['W2'] = weight_scale[1] * np.random.randn(num_filters[1], num_filters[0], filter_size, filter_size)
    self.params['b2'] = np.zeros([num_filters[1]])
    self.params['W3'] = weight_scale[2] * np.random.randn(num_filters[2], num_filters[1], filter_size, filter_size)
    self.params['b3'] = np.zeros([num_filters[2]])
    self.params['W4'] = weight_scale[3] * np.random.randn(num_filters[2]*H*W/16, num_classes)
    self.params['b4'] = np.zeros([num_classes])

    
    self.bn_params = [{'mode': 'train'} for i in xrange(4)]
    
    for k, v in self.params.iteritems():
      self.params[k] = v.astype(dtype)
    
    
  def loss(self, X, y=None, hardware_sampling=0):
    """
    Evaluate loss and gradient for the three-layer convolutional network.
    
    Input / output: Same API as TwoLayerNet in fc_net.py.
    """

    mode = 'test' if y is None else 'train'
    for bn_param in self.bn_params:
        bn_param[mode] = mode
    
    
    W1, b1 = self.params['W1'], self.params['b1']
    W2, b2 = self.params['W2'], self.params['b2']
    W3, b3 = self.params['W3'], self.params['b3']
    W4, b4 = self.params['W4'], self.params['b4']

    # pass conv_param to the forward pass for the convolutional layer
    filter_size = W1.shape[2]
    conv_param = {'stride': 1, 'pad': (filter_size - 1) / 2}

    # pass pool_param to the forward pass for the max-pooling layer
    pool_param = {'pool_height': 2, 'pool_width': 2, 'stride': 2}

    scores = None

    #out, conv1_cache = conv_sigmoid_pool_forward(X,W1,b1,conv_param,pool_param)
    ##layer1:
    a, conv_cache = conv_forward_fast(X, W1, b1, conv_param)
    
    if hardware_sampling==0:
	s, relu_cache = sigmoid_forward(a)
    if hardware_sampling==1:
          f = h5py.File('/home/burc/MATLAB/myfilesample3fullresetnonoiseVth06.h5','r') 
          data = f.get('dataset1') 
          data = np.transpose(np.array(data)) 
          #print data.shape
          indices=np.array(np.clip(np.round(50*a)+250,1,500))-1
          randsel=10000*np.random.rand(10000,a.shape[1],a.shape[2],a.shape[3])+1
          randint=np.array(np.floor(randsel))-1
          s = data[indices.astype(int),randint.astype(int)]	
	  relu_cache=None
	  print 'layer 1 done'
    out, pool_cache = max_pool_forward_fast(s, pool_param)
    conv1_cache = (conv_cache, relu_cache, pool_cache)


    #layer2:
    #out, conv2_cache = conv_sigmoid_pool_forward(out,W2,b2,conv_param,pool_param)
    
    a, conv_cache = conv_forward_fast(out, W2, b2, conv_param)
    if hardware_sampling==0:
	s, relu_cache = sigmoid_forward(a)
    if hardware_sampling==1:
          #f = h5py.File('/home/burc/MATLAB/myfilesample1fullresetnonoiseVth06.h5','r') 
          #data = f.get('dataset1') 
          #data = np.transpose(np.array(data)) 
          #print data.shape
          indices=np.array(np.clip(np.round(50*a)+250,1,500))-1
          randsel=10000*np.random.rand(10000,a.shape[1],a.shape[2],a.shape[3])+1
          randint=np.array(np.floor(randsel))-1
          s = data[indices.astype(int),randint.astype(int)]	
	  relu_cache=None
	  print 'layer 2 done'
    out, pool_cache = max_pool_forward_fast(s, pool_param)
    conv2_cache = (conv_cache, relu_cache, pool_cache)

    #layer3:
    #out, conv3_cache = conv_sigmoid_forward(out,W3,b3,conv_param)
    a, conv_cache = conv_forward_fast(out, W3, b3, conv_param)
    if hardware_sampling==0:
	out, relu_cache = sigmoid_forward(a)
    if hardware_sampling==1:
          #f = h5py.File('/home/burc/MATLAB/myfilesample1fullresetnonoiseVth06.h5','r') 
          #data = f.get('dataset1') 
          #data = np.transpose(np.array(data)) 
          #print data.shape
          indices=np.array(np.clip(np.round(50*a)+250,1,500))-1
          randsel=10000*np.random.rand(10000,a.shape[1],a.shape[2],a.shape[3])+1
          randint=np.array(np.floor(randsel))-1
          out = data[indices.astype(int),randint.astype(int)]	
	  relu_cache=None
	  print 'layer 3 done'
    conv3_cache = (conv_cache, relu_cache)
    
    

    out, affine_cache = affine_forward(out, W4, b4)

    if hardware_sampling==0:
	scores, sig_cache = sigmoid_forward(out) 
    if hardware_sampling==1:
          #f = h5py.File('/home/burc/MATLAB/myfilesample1fullresetnonoiseVth06.h5','r') 
          #data = f.get('dataset1') 
          #data = np.transpose(np.array(data)) 
          #print data.shape
          print out.shape
          indices=np.array(np.clip(np.round(50*out)+250,1,500))-1
          randsel=10000*np.random.rand(10000,out.shape[1])+1
          randint=np.array(np.floor(randsel))-1
          scores = data[indices.astype(int),randint.astype(int)]	
	  sig_cache=None
	  print 'layer 4 done'






    #scores, bn_cache = batchnorm_forward(out, gamma4, beta4, self.bn_params[3])
    
    if y is None:
      return scores
    loss, grads = 0, {}
   
    loss, dscores = softmax_loss(scores, y)
    loss += 0.5 * self.reg * (np.sum(W1*W1) + np.sum(W2*W2) + np.sum(W3*W3) + np.sum(W4*W4))
    #dx, dgamma4, dbeta4 = batchnorm_backward(dscores, affine_cache)

    dx = sigmoid_backward(dscores, sig_cache)
    dx, dW4, db4 = affine_backward(dx, affine_cache)
    dx, dW3, db3 = conv_sigmoid_backward(dx, conv3_cache)
    dx, dW2, db2 = conv_sigmoid_pool_backward(dx, conv2_cache)
    dx, dW1, db1= conv_sigmoid_pool_backward(dx, conv1_cache)
    dW1 += self.reg * W1
    dW2 += self.reg * W2
    dW3 += self.reg * W3
    dW4 += self.reg * W4
    grads.update({'W1':dW1, 'b1':db1, 'W2':dW2, 'b2':db2, 'W3':dW3, 'b3':db3, 'W4':dW4, 'b4':db4})
   
    
    return loss, grads
  
