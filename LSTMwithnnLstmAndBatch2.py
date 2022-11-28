#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This code is based on the tutorial by Sean Robertson <https://github.com/spro/practical-pytorch> found here:
https://pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html

Students *MAY NOT* view the above tutorial or use it as a reference in any way.
"""

from __future__ import unicode_literals, print_function, division

import argparse
import logging
import random
import time
import math
from io import open
import tkinter
import numpy as np

import matplotlib

global forward_pass
forward_pass = True

# if you are running on the gradx/ugradx/ another cluster,
# you will need the following line
# if you run on a local machine, you can comment it out
# matplotlib.use('agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import torch
import torch.nn as nn
import torch.nn.functional as F
from nltk.translate.bleu_score import corpus_bleu
from torch import optim

# we are forcing the use of cpu, if you have access to a gpu, you can set the flag to "cuda"
# make sure you are very careful if you are using a gpu on a shared cluster/grid,
# it can be very easy to confict with other people's jobs.
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


SOS_token = "<SOS>"
EOS_token = "<EOS>"

SOS_index = 0
EOS_index = 1
MAX_LENGTH = 200
BATCH_SIZE = 4


class Vocab:
    """ This class handles the mapping between the words and their indicies
    """

    def __init__(self, lang_code):
        self.lang_code = lang_code
        self.word2index = {}
        self.word2count = {}
        self.index2word = {SOS_index: SOS_token, EOS_index: EOS_token}
        self.n_words = 2  # Count SOS and EOS

    def add_sentence(self, sentence):
        for word in sentence.split(' '):
            self._add_word(word)

    def _add_word(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1


######################################################################


def split_lines(input_file):
    """split a file like:
    first src sentence|||first tgt sentence
    second src sentence|||second tgt sentence
    into a list of things like
    [("first src sentence", "first tgt sentence"),
     ("second src sentence", "second tgt sentence")]
    """
    logging.info("Reading lines of %s...", input_file)
    # Read the file and split into lines
    lines = open(input_file, encoding='utf-8').read().strip().split('\n')
    # Split every line into pairs
    pairs = [l.split('|||') for l in lines]
    return pairs


def make_vocabs(src_lang_code, tgt_lang_code, train_file):
    """ Creates the vocabs for each of the langues based on the training corpus.
    """
    src_vocab = Vocab(src_lang_code)
    tgt_vocab = Vocab(tgt_lang_code)

    train_pairs = split_lines(train_file)

    for pair in train_pairs:
        src_vocab.add_sentence(pair[0])
        tgt_vocab.add_sentence(pair[1])

    logging.info('%s (src) vocab size: %s', src_vocab.lang_code, src_vocab.n_words)
    logging.info('%s (tgt) vocab size: %s', tgt_vocab.lang_code, tgt_vocab.n_words)

    return src_vocab, tgt_vocab


######################################################################

def tensor_from_sentence(vocab, sentence):
    """creates a tensor from a raw sentence
    """
    indexes = []
    for word in sentence.split():
        try:
            indexes.append(vocab.word2index[word])
        except KeyError:
            pass
            # logging.warn('skipping unknown subword %s. Joint BPE can produces subwords at test time which are not in vocab. As long as this doesnt happen every sentence, this is fine.', word)
    indexes.append(EOS_index)
    return torch.tensor(indexes, dtype=torch.long, device=device).view(-1, 1)


def tensors_from_pair(src_vocab, tgt_vocab, pair):
    """creates a tensor from a raw sentence pair
    """
    input_tensor = tensor_from_sentence(src_vocab, pair[0])
    target_tensor = tensor_from_sentence(tgt_vocab, pair[1])
    return input_tensor, target_tensor


######################################################################


class EncoderRNN(nn.Module):
    """the class for the enoder RNN"""

    def __init__(self, input_size, hidden_size):
        super(EncoderRNN, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.LSTM = nn.LSTM(hidden_size, hidden_size)
        self.embedding = nn.Embedding(input_size, hidden_size)

    def forward(self, input, hidden):
        # global forward_pass
        # if forward_pass:
        # embeds=self.embedding(input)
        # output, _ = self.LSTM(embeds.view(len(input), 1, -1))

        out1 = self.embedding(input).transpose(0, 1)
        global translationsMODE
        if translationsMODE == True:
            out1 = out1.transpose(0, 1).unsqueeze(0)

        output, hidden = self.LSTM(out1, hidden)
        return output, hidden

    def get_initial_hidden_state(self):  # This mislead us a lot
        return torch.zeros(1, BATCH_SIZE, self.hidden_size, device=device)

    def get_initial_hidden_state_not_batch(self):
        return torch.zeros(1, 1, self.hidden_size, device=device)


class AttnDecoderRNN(nn.Module):
    """the class for the decoder
    """

    def __init__(self, hidden_size, output_size, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout_p = dropout_p
        self.max_length = max_length
        self.dropout = nn.Dropout(self.dropout_p)
        self.embed = nn.Embedding(self.output_size, self.hidden_size)
        self.attention = nn.Linear(self.hidden_size * 2, self.max_length)
        self.attention_layers = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.LSTM = nn.LSTM(self.hidden_size, self.hidden_size)
        self.softmax = nn.LogSoftmax(dim=1)
        self.softmax_helper = nn.Linear(self.hidden_size, self.output_size)

    def forward(self, input, hidden, encoder_outputs):
        """runs the forward pass of the decoder
        returns the log_softmax, hidden state, and attention_weights

        Dropout (self.dropout) should be applied to the word embeddings.
        """
        "*** YOUR CODE HERE ***"

        embedding = self.embed(input)
        embedding = self.dropout(embedding)

        global firstIteration
        if firstIteration == True:
            embedding = embedding.transpose(0, 1)
            firstIteration = False

        global translationsMODE
        if translationsMODE == True:
            embedding = embedding

        attention_weights = F.softmax(self.attention(torch.cat((embedding[0], hidden[0][0]), 1)), dim=1)

        output = torch.tanh(self.attention_layers(torch.cat((embedding[0], torch.bmm(attention_weights.unsqueeze(0),
                                                                                     encoder_outputs.unsqueeze(0))[0]),
                                                            1)))
        output, hidden = self.LSTM(output.unsqueeze(0), hidden)

        log_softmax = F.log_softmax(self.softmax_helper(output.squeeze(0)), dim=1)
        return log_softmax, hidden, attention_weights

    def get_initial_hidden_state(self):
        return torch.zeros(1, BATCH_SIZE, self.hidden_size, device=device)


#######################################################################

def train(input_tensor, target_tensor, encoder, decoder, optimizer, criterion, max_length=MAX_LENGTH):
    encoder_hidden = (encoder.get_initial_hidden_state(), encoder.get_initial_hidden_state())
    # for i in range(BATCH_SIZE):
    #     encoder_hidden += encoder.get_initial_hidden_state()

    global translationsMODE
    translationsMODE = False

    encoder.train()
    decoder.train()

    # Using a lot of the same logic from the translate function.

    optimizer.zero_grad()

    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)

    encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

    loss = 0

    for ei in range(input_length):  # Getting outputs from encoder
        encoder_output, encoder_hidden = encoder(
            input_tensor[ei], encoder_hidden)
        encoder_outputs[ei] = encoder_output[0, 0]

    sos_indexes = []
    for i in range(BATCH_SIZE):
        sos_indexes.append([SOS_index])

    decoder_input = torch.tensor(sos_indexes, device=device)

    decoder_hidden = encoder_hidden

    for di in range(target_length):
        decoder_output, decoder_hidden, decoder_attention = decoder(decoder_input, decoder_hidden, encoder_outputs)
        topv, topi = decoder_output.data.topk(1)

        decoder_input = topi.squeeze().detach().unsqueeze(0)

        for i in range(BATCH_SIZE):
            loss += criterion(decoder_output[i].unsqueeze(0), target_tensor[di][i])
            if topi[i].item() == "<EOS>":
                break

    loss.backward()
    optimizer.step()
    return loss.item()


######################################################################

def translate(encoder, decoder, sentence, src_vocab, tgt_vocab, max_length=MAX_LENGTH):
    """
    runs tranlsation, returns the output and attention
    """

    # switch the encoder and decoder to eval mode so they are not applying dropout
    encoder.eval()
    decoder.eval()

    global translationsMODE
    translationsMODE = True

    with torch.no_grad():
        input_tensor = tensor_from_sentence(src_vocab, sentence)
        input_length = input_tensor.size()[0]
        encoder_hidden = (encoder.get_initial_hidden_state_not_batch(), encoder.get_initial_hidden_state_not_batch())

        encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei],
                                                     encoder_hidden)
            encoder_outputs[ei] += encoder_output[0, 0]

        decoder_input = torch.tensor([[SOS_index]], device=device)

        decoder_hidden = encoder_hidden

        decoded_words = []
        decoder_attentions = torch.zeros(max_length, max_length)

        for di in range(max_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            decoder_attentions[di] = decoder_attention.data
            topv, topi = decoder_output.data.topk(1)
            if topi.item() == EOS_index:
                decoded_words.append(EOS_token)
                break
            else:
                decoded_words.append(tgt_vocab.index2word[topi.item()])

            decoder_input = topi.squeeze().detach().unsqueeze(0).unsqueeze(0)

        translationsMODE = False

        return decoded_words, decoder_attentions[:di + 1]


######################################################################

# Translate (dev/test)set takes in a list of sentences and writes out their transaltes
def translate_sentences(encoder, decoder, pairs, src_vocab, tgt_vocab, max_num_sentences=None, max_length=MAX_LENGTH):
    output_sentences = []
    for pair in pairs[:max_num_sentences]:
        output_words, attentions = translate(encoder, decoder, pair[0], src_vocab, tgt_vocab)
        output_sentence = ' '.join(output_words)
        output_sentences.append(output_sentence)
    return output_sentences


######################################################################
# We can translate random sentences  and print out the
# input, target, and output to make some subjective quality judgements:
#

def translate_random_sentence(encoder, decoder, pairs, src_vocab, tgt_vocab, n=1):
    for i in range(n):
        pair = random.choice(pairs)
        print('>', pair[0])
        print('=', pair[1])
        output_words, attentions = translate(encoder, decoder, pair[0], src_vocab, tgt_vocab)
        output_sentence = ' '.join(output_words)
        print('<', output_sentence)
        print('')


######################################################################

def show_attention(input_sentence, output_words, attentions):
    """visualize the attention mechanism. And save it to a file.
    Plots should look roughly like this: https://i.stack.imgur.com/PhtQi.png
    You plots should include axis labels and a legend.
    you may want to use matplotlib.
    """

    "*** YOUR CODE HERE ***"

    npattentions = np.array(attentions)

    global plotnumber, axlist

    axlist[plotnumber - 1].xaxis.tick_top()
    axlist[plotnumber - 1].xaxis.set_major_locator(ticker.MultipleLocator(1))
    axlist[plotnumber - 1].yaxis.set_major_locator(ticker.MultipleLocator(1))

    axlist[plotnumber - 1].imshow(npattentions)

    ticklabelx = [''] + input_sentence.split(' ') + ['<end>']
    ticklabely = [''] + output_words + ['<end>']
    axlist[plotnumber - 1].set_xticklabels(ticklabelx, rotation=90)
    axlist[plotnumber - 1].set_yticklabels(ticklabely)

    plotnumber = plotnumber + 1


def translate_and_show_attention(input_sentence, encoder1, decoder1, src_vocab, tgt_vocab):
    output_words, attentions = translate(
        encoder1, decoder1, input_sentence, src_vocab, tgt_vocab)
    print('input =', input_sentence)
    print('output =', ' '.join(output_words))
    show_attention(input_sentence, output_words, attentions)


def clean(strx):
    """
    input: string with bpe, EOS
    output: list without bpe, EOS
    """
    return ' '.join(strx.replace('@@ ', '').replace(EOS_token, '').strip().split())


######################################################################

def main():
    hidden_size = 256
    n_iters = 1000
    print_every = 50
    checkpoint_every = 10000
    initial_learning_rate = 0.001
    src_lang = 'dk'
    tgt_lang = 'en'
    train_file = 'data/traindata.txt'
    dev_file = 'data/validationdata.txt'
    test_file = 'data/testdata.txt'
    out_file = 'out.txt'
    load_checkpoint = None

    # process the training, dev, test files

    # Create vocab from training data, or load if checkpointed
    # also set iteration
    if load_checkpoint is not None:
        state = torch.load(load_checkpoint[0])
        iter_num = state['iter_num']
        src_vocab = state['src_vocab']
        tgt_vocab = state['tgt_vocab']
    else:
        iter_num = 0
        src_vocab, tgt_vocab = make_vocabs(src_lang, tgt_lang, train_file)

    encoder = EncoderRNN(src_vocab.n_words, hidden_size).to(device)
    decoder = AttnDecoderRNN(hidden_size, tgt_vocab.n_words).to(device)

    # encoder/decoder weights are randomly initilized
    # if checkpointed, load saved weights
    if load_checkpoint is not None:
        encoder.load_state_dict(state['enc_state'])
        decoder.load_state_dict(state['dec_state'])

    # read in datafiles
    train_pairs = split_lines(train_file)
    dev_pairs = split_lines(dev_file)
    test_pairs = split_lines(test_file)

    # set up optimization/loss
    params = list(encoder.parameters()) + list(decoder.parameters())  # .parameters() returns generator
    optimizer = optim.Adam(params, lr=initial_learning_rate)
    criterion = nn.NLLLoss()

    # optimizer may have state
    # if checkpointed, load saved state
    if load_checkpoint is not None:
        optimizer.load_state_dict(state['opt_state'])

    start = time.time()
    print_loss_total = 0  # Reset every print_every

    # Use nn.pad sequenec

    while iter_num < n_iters:
        iter_num += 1
        global firstIteration
        firstIteration = True
        inputList = []
        outputList = []
        tensors = []

        # training_pair = tensors_from_pair(src_vocab, tgt_vocab, random.choice(train_pairs))
        for i in range(BATCH_SIZE):
            tensors.append(tensors_from_pair(src_vocab, tgt_vocab, random.choice(train_pairs)))
        for i in range(BATCH_SIZE):
            inputList.append(tensors[i][0])
            outputList.append(tensors[i][1])
        batchInput = nn.utils.rnn.pad_sequence(inputList)
        batchOutput = nn.utils.rnn.pad_sequence(outputList)
        # input_tensor = training_pair[0]
        # target_tensor = training_pair[1]
        # loss = train(input_tensor, target_tensor, encoder,
        #              decoder, optimizer, criterion)
        loss = train(batchInput, batchOutput, encoder,
                     decoder, optimizer, criterion)
        print_loss_total += loss

        if iter_num % checkpoint_every == 0:
            state = {'iter_num': iter_num,
                     'enc_state': encoder.state_dict(),
                     'dec_state': decoder.state_dict(),
                     'opt_state': optimizer.state_dict(),
                     'src_vocab': src_vocab,
                     'tgt_vocab': tgt_vocab,
                     }
            filename = 'state_%010d.pt' % iter_num
            torch.save(state, filename)
            logging.debug('wrote checkpoint to %s', filename)

        if iter_num % print_every == 0:
            print("Iter:", iter_num, "/", n_iters)
            print_loss_avg = print_loss_total / print_every
            print_loss_total = 0
            temptime=time.time() - start
            print(f'time since start:{temptime:.2f} s')
            # translate from the dev set
            translate_random_sentence(encoder, decoder, dev_pairs, src_vocab, tgt_vocab, n=2)
            translated_sentences = translate_sentences(encoder, decoder, dev_pairs, src_vocab, tgt_vocab)

            references = [[clean(pair[1]).split(), ] for pair in dev_pairs[:len(translated_sentences)]]
            candidates = [clean(sent).split() for sent in translated_sentences]
            dev_bleu = corpus_bleu(references, candidates)
            print('Dev BLEU score: %.2f', dev_bleu)
            # logging.info('Dev BLEU score: %.2f', dev_bleu)

    # translate test set and write to file
    translated_sentences = translate_sentences(encoder, decoder, test_pairs, src_vocab, tgt_vocab)
    with open(out_file, 'wt', encoding='utf-8') as outf:
        for sent in translated_sentences:
            outf.write(clean(sent) + '\n')

    global axlist
    fig, ax = plt.subplots(nrows=2, ncols=2)

    axlist = [ax[0, 0], ax[1, 0], ax[0, 1], ax[1, 1]]

    global plotnumber
    plotnumber = 1

    # Visualizing Attention
    translate_and_show_attention("on p@@ eu@@ t me faire confiance .", encoder, decoder, src_vocab, tgt_vocab)
    translate_and_show_attention("j en suis contente .", encoder, decoder, src_vocab, tgt_vocab)
    translate_and_show_attention("vous etes tres genti@@ ls .", encoder, decoder, src_vocab, tgt_vocab)
    translate_and_show_attention("c est mon hero@@ s ", encoder, decoder, src_vocab, tgt_vocab)

    plt.show()


if __name__ == '__main__':
    main()