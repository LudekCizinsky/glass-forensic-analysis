import numpy as np
from tqdm import tqdm
from icecream import ic
from sklearn.preprocessing import OneHotEncoder

from ...base import BaseClassifier
from ...utils import validate_feature_matrix, validate_target_vector
from ...metrics import se, mse, cross_entropy 
from ._autograd import Var
from ._dense_layer import DenseLayer
from ._helper import convert_to_var, softmax, hot_encode

class NeuralNetworkClassifier(BaseClassifier):
    def __init__(self, layers=[], loss='squared_error', name='NeuralNetworkClassifier'):
        super().__init__()

        self.name = name

        self.X = self.y = self.n = self.p = None
        self.y_hot = None
        self.fitted = False

        self.layers = layers
        self.parameters = self._parameters()

        if loss == 'cross_entropy':
            self.loss = cross_entropy
        elif loss == 'squared_error':
            self.loss = se
        elif loss == 'mean_squared_error':
            self.loss = mse
        else:
            raise NotImplementedError(f"{loss} not yet implemented. Choose from ['cross_entropy', 'squared_error', 'mean_squared_error']") 

    def add(self, layer):
        self.layers.append(layer)

    def forward(self, X):
        """
        Computes the forward pass of the MLP: x = layer(x) for each layer in layers
        """
        for layer in self.layers:
            X = layer.forward(X)

        return X

    def fit(self, X, y, batch_size=1, epochs=1000, lr = 0.01, verbose=0):
        self.X = validate_feature_matrix(X)
        self.X = convert_to_var(self.X)
        self.y = y 

        self.n, self.p = self.X.shape
        self.k = len(np.unique(y))
        
        # add output layer
        output_layer = DenseLayer(self.layers[-1].neurons(), self.k, activation='softmax', name='Output')
        self.add(output_layer)

        # populate label-intcode dictionaries
        unique_classes = np.unique(y)

        self.label = {k: unique_classes[k] for k in range(self.k)}
        self.intcode = {unique_classes[k]:k for k in range(self.k)}

        # one hot encode y (into nxk matrix of Vars)
        y_hot = hot_encode(self.y, self.intcode)
        self.y_hot = convert_to_var(y_hot)

        # compute batch size
        batch_size = int(X.shape[0] * batch_size)

        # training loop
        self.training_history = []
        for epoch in tqdm(range(epochs)):
            if batch_size < self.n :
                batch_idxs = np.random.choice(list(range(self.n)), batch_size, replace=False) 
                X_batch = self.X[batch_idxs]
                y_batch = self.y_hot[batch_idxs]
            else: 
                X_batch = self.X
                y_batch = self.y_hot

            # get the probabilities for each datapoint of belonging to each class
            probs = self.forward(X_batch) # n x k matrix of probs for each data point for each class 

            # compute loss on one-hot encoded target matrix

            assert not np.any(probs < Var(0.0)), 'probs must be > 0, due to softmax'
            loss = self.loss(y_batch, probs)

            # append loss to training history
            self.training_history.append(loss.v)

            # zeroing out gradients
            for param in self.parameters:
                param.grad = 0.0

            # recompute gradients
            loss.backward()

            # update weights
            for param in self.parameters: 
                param.v -= lr * param.grad

            if verbose:
                if epoch % verbose == 0:
                    print(epoch, loss)

        self.fitted = True

    def predict(self, X):
        probs = self.predict_proba(X)

        return np.argmax(probs, axis=1).astype(int)

    def predict_proba(self, X):
        X = convert_to_var(X)

        probs = self.forward(X) # probs for classes

        return softmax(probs) # softmaxed results

    def _parameters(self):
        """ Returns all the parameters of the layers as a 1d np array"""
        return np.hstack([layer.parameters() for layer in self.layers])

    def _total_parameters(self):
        return len(self.parameters)

    def summary(self):
        s = f"Name: {self.name}\n\n" 
        s += 'Layer\t\tWeight Dim\tBias Dim\tTotal Parameters\n'
        s += '=' * (len('Layer\t\tWeight Dim\tBias Dim\tTotal Parameters\n')+20) + '\n'
        for layer in self.layers:
            s += repr(layer) + '\n'
        if not self.fitted:
            s += 'Output Layer\tNot yet fitted\n'
        s += '=' * (len('Layer Name\tWeight Dim\tBias Dim\tTotal Parameters\n')+20) + '\n'
        s += f'\t\t\t\t\t\t{self._total_parameters()}'
        return s
