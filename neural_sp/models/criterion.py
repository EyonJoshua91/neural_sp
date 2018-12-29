#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 Kyoto University (Hirofumi Inaguma)
#  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)

"""Criterions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import numpy as np

import torch
import torch.nn.functional as F


def cross_entropy_lsm(logits, ys, y_lens, lsm_prob, size_average=False):
    """Compute cross entropy loss for label smoothing of sequence-to-sequence models.

    Args:
        logits (FloatTensor): `[B, T, vocab]`
        ys (LongTensor): Indices of labels. `[B, L]`.
        y_lens (list): A list of length `[B]`
        lsm_prob (float):
        size_average (bool):
    Returns:
        loss (FloatTensor): `[1]`

    """
    bs, _, vocab = logits.size()
    fill_val = lsm_prob / (vocab - 1)

    # Create one-hot vector
    ys_lsm = torch.zeros_like(logits).fill_(fill_val)
    for b in range(bs):
        for t in range(y_lens[b]):
            ys_lsm[b, t, ys[b, t]] = 1 - lsm_prob

    # Compute XE for label smoothing
    log_probs = F.log_softmax(logits, dim=-1)
    loss = np.sum([(- ys_lsm[b, :y_lens[b]] * log_probs[b, :y_lens[b]]).sum()
                   for b in range(bs)])
    if size_average:
        loss /= bs
    return loss


def kldiv_lsm_ctc(logits, y_lens, lsm_prob, size_average=False):
    """Compute KL divergence loss for label smoothing of CTC models.

    Args:
        logits (FloatTensor): `[B, T, vocab]`
        y_lens (list): A list of length `[B]`
        lsm_prob (float):
        size_average (bool):
    Returns:
        loss (FloatTensor): `[1]`

    """
    bs, _, vocab = logits.size()

    # Create uniform distribution
    log_uniform = torch.zeros_like(logits).fill_(math.log(lsm_prob))

    # Compute XE for label smoothing
    probs = F.softmax(logits, dim=-1)
    log_probs = F.log_softmax(logits, dim=-1)
    kl_div = torch.mul(probs, log_probs) - torch.mul(probs, log_uniform)
    loss = np.sum([kl_div[b, :y_lens[b]].sum() for b in range(bs)])
    if size_average:
        loss /= bs
    return loss


def focal_loss(logits, ys, y_lens, gamma, size_average=False):
    """Compute focal loss.

    Args:
        logits (FloatTensor): `[B, T, vocab]`
        ys (LongTensor): Indices of labels. `[B, L]`.
        y_lens (list): A list of length `[B]`
        gamma (float):
        size_average (bool):
    Returns:
        loss (FloatTensor): `[1]`

    """
    bs = ys.size(0)

    # Create one-hot vector
    ys_onehot = torch.ones_like(logits)
    for b in range(bs):
        for t in range(y_lens[b]):
            ys_onehot[b, t, ys[b, t]] = 1

    # Compute focal loss
    log_probs = F.log_softmax(logits, dim=-1)
    probs = F.softmax(logits, dim=-1)
    # probs = logits.exp() / logits.exp().sum(-1).unsqueeze(-1)
    ones = torch.ones_like(log_probs)
    # print(probs[0, y_lens[0] - 1])
    loss = np.sum([(- ys_onehot[b, :y_lens[b]] * torch.pow(ones[b, :y_lens[b]] - probs[b, :y_lens[b]], gamma) * log_probs[b, :y_lens[b]]).sum()
                   for b in range(bs)])
    if size_average:
        loss /= bs
    return loss
