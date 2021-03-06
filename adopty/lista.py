import torch
import numpy as np

from ._compat import AVAILABLE_CONTEXT


class Lista(torch.nn.Module):
    """L-ISTA network for the LASSO problem
    """
    def __init__(self, D, n_layers, name="LISTA", ctx=None):
        if ctx:
            msg = "Context {} is not available on this computer."
            assert ctx in AVAILABLE_CONTEXT, msg.format(ctx)
        else:
            ctx = AVAILABLE_CONTEXT[0]

        self._ctx = ctx
        self.n_layers = n_layers

        self.D = np.array(D)
        self.B = D.dot(D.T)
        self.L = np.linalg.norm(self.B, ord=2)

        self.params = []

        self.init_network_torch()

    def init_network_torch(self, params=[]):
        super().__init__()
        n_atoms = self.D.shape[0]

        self.params = []
        for i in range(self.n_layers):
            if len(params) > 0:
                param = params.pop(0)
            else:
                param = [np.eye(n_atoms) - self.B / self.L, self.D.T / self.L]
            Wz = torch.nn.Parameter(torch.from_numpy(param[0]))
            Wx = torch.nn.Parameter(torch.from_numpy(param[1]))

            self.params += [(Wz, Wx)]

    def forward(self, x, lmbd, z0=None):
        # Compat numpy
        if isinstance(x, np.ndarray):
            x = torch.autograd.Variable(torch.Tensor(x).double())

        # Compute the first layer
        p = self.params[0]
        z_hat = x.matmul(p[1])
        if z0:
            z_hat += z0.matmul(p[0])
        z_hat = torch.nn.functional.softshrink(z_hat, lmbd / self.L)

        # Compute the following layers
        for p in self.params[1:]:
            z_hat = z_hat.matmul(p[0]) + x.matmul(p[1])
            z_hat = torch.nn.functional.softshrink(z_hat, lmbd / self.L)

        return z_hat
