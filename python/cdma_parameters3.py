#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2014 Achilleas Anastasopoulos, Zhe Feng.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
import random
import numpy
from gnuradio import digital,trellis
import math
import cdma
from fractions import Fraction,gcd
from operator import mul
#from gnuradio.digital.utils import tagged_streams


class cdma_parameters:

    def __init__(self):
	"""
 Description:
 This file contains most of the basic design parameters of the cdma system. Users can modify these parameters for their applications. 
 
 header parameters:
 length_tag_name is the length tag key used in the packet header generator. 
 num_tag_name is the num tag key used in the packet header generator. 
 bits_per_header denotes the number of bits per header. 
 header_mod denotes the modulation scheme for header symbols. In this CDMA system, the header is BPSK modulated. 
 header_formatter generates the header by using these above parameters. 
 To avoid evaluation error in symbols per header, bits per header and then symbols per header are automatically adjusted if error occurs. 

 modulation parameters:
 payload_mod is a list containing constellation objects to be used in a possibly adaptive modulation setup.

 coding parameters:
 A list of fsm objects to be used in conjunction with each constellation object defined above.
 The bits_per_coded_symbol of trellis codes are compared to their corresponding bits_per_symbol of modulations to ensure consistency.
 
 payload parameters:
 There are four parameters are set by the users.
 payload_bytes_per_frame is preset by the user to denote the number of payload bytes per frame. 
 symbols_per_frame is preset by the user to denote the number of symbols per frame. 
 bits_per_uncoded_symbols is preset by the user.
 crc_bytes denotes the number of crc bytes per frame generated by the stream crc32 generator. 
 crc_coded_payload_bytes_per_frame denotes the payload bytes per frame after outer crc code. 
 crc_coded_payload_symbols_per_frame denotes the the payload symbols per frame after outer crc code. 
 trellis_coded_payload_symbols_per_frame denotes the payload symbols per frame after inner trellis code.
 Trellis_coded_bytes_per_frame is the number of bytes after trellis coding.
 additional_symbols_per_frame denotes the additional symbols needed to satisfy the symbols_per_frame. It must be greater or equal to zero.
 additional_bytes_per_frame denotes the additional bytes per frame. Since we don't encode the additional bits.
 redudant_bytes_percent is the percent of the additional bytes in total bytes.
 
 training parameters:
 training_long denotes the randomly generated training sequence with the same length to symbols_per_frame. 
 training is the adjusted training sequence (maybe shorter than one frame) 
 training_percent is the percentage of power for training at the transmitter. It takes value in [0,100]. 
 
 cdma parameters:
 chips_per_symbol denotes the spreading factor which is ratio of the chip rate to baseband symbol rate.
 chips_per_frame denotes the total number of chips per frame. 
 pulse_training denotes the spreading code sequence for the training channel. 
 pulse_data denotes the spreading code sequence for the data channel. Pulse_training and pulse_data should better be orthogonal. 

 timing parameters:
 peak_o_var denotes the output correlation peak over variance value of the matched filter in frequency timing estimator. It is used for the rise and fall threshold factor of the peak detector in the frequency timing estimator. 
 EsN0dBthreshold is the SNR threshold of switching between Acquisition and Tracking mode when auto switch mode is selected. If the estimated SNR is greater than EsN0dBthreshold, the system switches to tracking mode automatically and vice versa. 
 epsilon is a small number used in estimating the SNR to avoid division by zero, etc. 
 n_filt denotes the number of matched filters used in the frequency timing estimator. 
 freqs denotes the center frequencies of the matched filters in the frequency timing estimator. These freqs values are normalized to the symbol rate. 

	"""


print "CDMA PARAMETERS : for adaptive modulation"

prefix="/home/anastas/gr-cdma/"  # put the prefix of your gr-cdma trunk

length_tag_name = "packet_len"
num_tag_name = "packet_num"

# header info
bits_per_header=12+12+8+4;  #Zhe Changed 12+16+8 to 12+12+8 because only 12 bits not 16 bits are needed. 4 bits indicating modulation and code mode.

header_mod = digital.constellation_bpsk();
symbols_per_header = bits_per_header/header_mod.bits_per_symbol()
if (1.0*bits_per_header)/header_mod.bits_per_symbol() != symbols_per_header:
  print "Error in evaluating symbols per header; adjusting bits per header"
  bits_per_header=(symbols_per_header+1)*header_mod.bits_per_symbol()
  symbols_per_header = bits_per_header/header_mod.bits_per_symbol()
#header_formatter = cdma.packet_header(bits_per_header,length_tag_name,num_tag_name,header_mod.bits_per_symbol());

#header_formatter = digital.packet_header_default(bits_per_header,  length_tag_name,num_tag_name,header_mod.bits_per_symbol());
#tcm_indicator_symbols_per_frame=4; #Zhe added, 4 bits are used as tcm mode indicator, it is used as a part of header.

# Achilles' comment: this may change later when filler bits are introduced...
print "bits_per_header=",bits_per_header
print "symbols_per_header=",symbols_per_header
#print "tcm_indicator_symbols_per_frame=",tcm_indicator_symbols_per_frame
print "\n"

#trellis coding and modulation info

payload_mod = [digital.constellation_qpsk(),digital.constellation_8psk(),digital.constellation_16qam()]

pdir=prefix+"/python/fsm_files/"
fsm=[pdir+"awgn2o2_1.fsm", pdir+"awgn2o3_8ungerboecka.fsm",pdir+"awgn2o4_8_ungerboeckc.fsm"]
uncoded_fsm=[trellis.fsm(2,2,[1,0,0,1]),trellis.fsm(3,3,[1,0,0,0,1,0,0,0,1]),trellis.fsm(4,4,[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])]

bits_per_coded_symbol=[int(math.log(trellis.fsm(fsm[i]).O(),2)) for i in range(len(payload_mod))]

#coding_rate=[Fraction(int(math.log(trellis.fsm(fsm[i]).I(),2)), int(math.log(trellis.fsm(fsm[i]).O(),2))) for i in range(len(fsm))]

if bits_per_coded_symbol!=[payload_mod[i].bits_per_symbol() for i in range(len(payload_mod))]:
  print "Error in selecting trellis code and modulation pairs."

print "bits_per_coded_symbol =", bits_per_coded_symbol, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"
#print "coding rates for trellis codes =", coding_rate, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"


#payload info
payload_bytes_per_frame = 50;	# set by user
symbols_per_frame = 260; # symbols per frame set by user

#Achilles comment: this should be log_2(fsm.I)
bits_per_uncoded_symbol = 2; # bits per uncoded symbols of payload

# the parameters for crc as an outer code. 
crc_bytes=4; 
crc_coded_payload_bytes_per_frame = payload_bytes_per_frame + crc_bytes;  #crc as the outer code, code it first.

# Achilles' comment: there is an assumption here that (50+4)8 will be a multiple of k. You need to stuff BITS in here
crc_coded_payload_symbols_per_frame = crc_coded_payload_bytes_per_frame*8/bits_per_uncoded_symbol; #crc coded payload symbols.

trellis_coded_payload_symbols_per_frame = crc_coded_payload_symbols_per_frame; #coded payload symbols equal the uncoded payload symbols.

additional_symbols_per_frame = symbols_per_frame - trellis_coded_payload_symbols_per_frame - symbols_per_header ;

if additional_symbols_per_frame < 0:
  print "Error in setting symbols per frame. To form a frame with set payload_bytes_per_frame, you should set a larger number of symbols per frame"

# Achilles' comment: assumption that this is a multiple of 8 !!!
additional_bytes_per_frame = [additional_symbols_per_frame * header_mod.bits_per_symbol()/8 for i in range(len(payload_mod))]; 

trellis_coded_payload_bytes_per_frame = [trellis_coded_payload_symbols_per_frame*payload_mod[i].bits_per_symbol()/8 for i in range(len(payload_mod))]

redudant_bytes_percents = [(1.0*additional_bytes_per_frame[i])/(trellis_coded_payload_bytes_per_frame[i]+additional_bytes_per_frame[i]) for i in range(len(additional_bytes_per_frame))];
print "payload_bytes_per_frame=", payload_bytes_per_frame
print "symbols_per_frame=", symbols_per_frame

print "trellis_coded_payload_symbols_per_frame=",trellis_coded_payload_symbols_per_frame, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"
print "trellis_coded_payload_bytes_per_frame=", trellis_coded_payload_bytes_per_frame, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"

print "additional_symbols_per_frame=",additional_symbols_per_frame, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"
print "additional_bytes_per_frame=", additional_bytes_per_frame, " for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] respectively.\n"
print "you have wasted",redudant_bytes_percents,"percent of bytes per payload for [uncoded QPSK, rate 2/3 cc &8PSK, rate 2/4 cc &16QAM] with this symbols_per_frame setting.\n"
print "\n"


# training info
numpy.random.seed(666)
training_long = (2*numpy.random.randint(0,2,symbols_per_frame)-1+0j)

training_length = symbols_per_frame; # number of non-zero training symbols
if training_length > symbols_per_frame:
  print "Error in training length evaluation"
  training_length = symbols_per_frame
training=training_long[0:training_length];
training_percent = 50; # percentage of transmitted power for training
print "training_length =", training_length
print "\n"

# cdma parameters
chips_per_symbol=8;	
chips_per_frame = chips_per_symbol*symbols_per_frame
pulse_training = numpy.array((1,1,1,1,-1,1,1,-1))+0j
pulse_data =numpy.array((-1,1,-1,1,-1,-1,-1,-1))+0j

# scaling factor at the receiver
rx_scaling_factor=[1,1,(float(training_percent)/100)**0.5*chips_per_symbol]

#timing parameters
peak_o_var = training_percent*symbols_per_frame*chips_per_symbol/(100+training_percent) #peak over variance for matched filter output 
EsN0dBthreshold = 10; 	# the threshold of switching from Acquisition to Tracking mode automatically.
epsilon = 1e-6; 	#tolerance
n_filt = 21;		# numbers of filters for the frequency/timing acquisition block
df1=1.0/(2*symbols_per_frame*chips_per_symbol) # Normalized (to chip rate) frequency interval due to training length
pll_loop_bw=0.005 # normailzed to symbol rate
df2=pll_loop_bw/chips_per_symbol # Normalized (to chip rate) frequency interval due to PLL
#df=max(df1,df2) # either a different frequency branch or the PLL will correct for it
df=df1
freqs=[(2*k-n_filt+1)*df/2 for k in range(n_filt)];	#Normalized frequency list.

#print "Normalized frequency interval = max(", df1, " , ", df2, ")=", df
print "Normalized frequency interval = ", df
print "Normalized frequency unsertainty range = [", freqs[0], " , ", freqs[-1], "]"