# -*- coding: utf-8 -*-
"""Piano_Hands.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/asigalov61/Piano-Hands/blob/main/Piano_Hands.ipynb

# Piano Hands (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

Credit for GPT2-RGA code used in this colab goes out @ Sashmark97 https://github.com/Sashmark97/midigen and @ Damon Gwinn https://github.com/gwinndr/MusicTransformer-Pytorch

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2022

***

# (GPU CHECK)
"""

#@title nvidia-smi gpu check
!nvidia-smi

"""# (SETUP ENVIRONMENT)"""

#@title Install all dependencies (run only once per session)

!git clone https://github.com/asigalov61/Piano-Hands
!pip install torch
!pip install tqdm
!pip install matplotlib

!pip install torch-summary
!pip install sklearn

#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os
import tqdm
from tqdm import tqdm
import random
import secrets
from collections import OrderedDict

if not os.path.exists('/content/Dataset'):
    os.makedirs('/content/Dataset')

print('Loading TMIDIX and GPT2RGAX modules...')
os.chdir('/content/Piano-Hands/')
import TMIDIX
from GPT2RGAX import *

import matplotlib.pyplot as plt
from torchsummary import summary
from sklearn import metrics

os.chdir('/content/')

"""# (FROM SCRATCH) Download and process MIDI dataset"""

# Commented out IPython magic to ensure Python compatibility.
#@title Download and unzip ASAP Dataset MIDI scores set

#@markdown https://github.com/fosfrancesco/asap-dataset

#@markdown PLEASE NOTE: The dataset is quite small so results may vary
# %cd /content/Dataset
!wget --no-check-certificate -O 'ASAP-Dataset-MIDI-Scores.zip' "https://onedrive.live.com/download?cid=8A0D502FC99C608F&resid=8A0D502FC99C608F%2118750&authkey=AHVj3_h3exo_tcY"
!unzip 'ASAP-Dataset-MIDI-Scores.zip'
!rm 'ASAP-Dataset-MIDI-Scores.zip'
# %cd /content/

"""# (PROCESS)"""

#@title Process MIDIs with TMIDIX MIDI processor

sorted_or_random_file_loading_order = False # Sorted order is NOT usually recommended
dataset_ratio = 1 # Change this if you need more data


print('TMIDIX MIDI Processor')
print('Starting up...')
###########

files_count = 0

gfiles = []

events_matrix_final = []

times = []

###########

print('Loading MIDI files...')
print('This may take a while on a large dataset in particular.')

dataset_addr = "/content/Dataset"
# os.chdir(dataset_addr)
filez = list()
for (dirpath, dirnames, filenames) in os.walk(dataset_addr):
    filez += [os.path.join(dirpath, file) for file in filenames]
print('=' * 70)

if filez == []:
    print('Could not find any MIDI files. Please check Dataset dir...')
    print('=' * 70)

print('Randomizing file list...')
random.shuffle(filez)

print('Processing MIDI files. Please wait...')
for f in tqdm(filez[:int(len(filez) * dataset_ratio)]):
    try:
        fn = os.path.basename(f)
        fn1 = fn.split('.')[0]

        #print('Loading MIDI file...')
        score = TMIDIX.midi2score(open(f, 'rb').read())

        
        itrack = 1

        events_matrix1 = []
        events_matrix2 = []

        for event in score[1]:         
           if event[0] == 'note':
              events_matrix1.append(event)

        for event in score[2]:         
           if event[0] == 'note':
              events_matrix2.append(event)
        
        events_matrix1.sort(key=lambda x: x[4], reverse=True)
        events_matrix1.sort(key=lambda x: x[1])

        events_matrix2.sort(key=lambda x: x[4], reverse=True)
        events_matrix2.sort(key=lambda x: x[1])       


        if len(events_matrix1) > 0 and len(events_matrix2) > 0:
          avg_ptc1 = sum([y[4] for y in events_matrix1]) / len([y[4] for y in events_matrix1])
          avg_ptc2 = sum([y[4] for y in events_matrix2]) / len([y[4] for y in events_matrix2])

          if avg_ptc1 > avg_ptc2:
            #print('found')

            events_matrix3 = []

            for e in events_matrix1:
              e.extend(['right'])
              events_matrix3.append(e)
             
            for e in events_matrix2:
              e.extend(['left'])
              events_matrix3.append(e)

            events_matrix3.sort(key=lambda x: x[4], reverse=True)
            events_matrix3.sort(key=lambda x: x[1])

            events_matrix4 = [131]

            pe = events_matrix3[0]
            for e in events_matrix3[1:]:
              time = e[1]-pe[1]

              ptc = max(1, min(127, e[4]))

              hand = e[6]

              if hand == 'right':
                handt = 129
              else:
                handt = 128

              #events_matrix4.extend([ptc, handt])
              
              if time == 0:
                events_matrix4.extend([ptc, handt])

              else:
               events_matrix4.extend([130])
               events_matrix4.extend([ptc, handt])

              pe = e

            events_matrix_final.extend(events_matrix4)

            files_count += 1
        
    except KeyboardInterrupt:
        print('Saving current progress and quitting...')
        break  

    except:
        print('Bad MIDI:', f)
        continue

print('=' * 70)
print('Done!')   
print('=' * 70)

print('Resulting Stats:')
print('=' * 70)
print('Total good MIDI Files:', files_count)
print('=' * 70)

print('Total INTs:', len(events_matrix_final))
print('Minimum INT:', min(events_matrix_final))
print('Maximum INT:', max(events_matrix_final))
print('Unique INTs:', len(set(events_matrix_final)))
print('Zero INTs:', events_matrix_final.count(0))
print('=' * 70)

"""# (LOAD INTs)"""

#@title Load processed INTs

SEQ_LEN = max_seq

BATCH_SIZE = 4 # Change this to your specs

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

print('=' * 50)
print('Loading training data...')

data_train, data_val = torch.Tensor(events_matrix_final), torch.Tensor(events_matrix_final[:8193])

class MusicSamplerDataset(Dataset):
    def __init__(self, data, seq_len):
        super().__init__()
        self.data = data
        self.seq_len = seq_len

    def __getitem__(self, index):

        idx = random.randint(0, (self.data.size(0) - self.seq_len-1))

        x = self.data[idx: idx + self.seq_len].long()
        trg = self.data[(idx+1): (idx+1) + self.seq_len].long()
        
        return x, trg

    def __len__(self):
        return self.data.size(0)

train_dataset = MusicSamplerDataset(data_train, SEQ_LEN)
val_dataset   = MusicSamplerDataset(data_val, SEQ_LEN)
train_loader  = DataLoader(train_dataset, batch_size = BATCH_SIZE)
val_loader    = DataLoader(val_dataset, batch_size = BATCH_SIZE)

print('=' * 50)
print('Total INTs in the dataset', len(events_matrix_final))
print('Total unique INTs in the dataset', len(set(events_matrix_final)))
print('Max INT in the dataset', max(events_matrix_final))
print('Min INT in the dataset', min(events_matrix_final))
print('=' * 50)
print('Length of the dataset:',len(train_dataset))
print('Number of batched samples per epoch:', len(events_matrix_final) // max_seq // BATCH_SIZE)
print('=' * 50)
print('Sample train dataset:', train_dataset[0])
print('Sample val dataset:', val_dataset[0])
print('=' * 50)
print('Train loader length:', len(train_loader))
print('Val loader length:', len(val_loader))
print('=' * 50)
print('Done! Enjoy! :)')
print('=' * 50)

"""# (TRAIN)

# Train the model
"""

#@title Train

DIC_SIZE = 132

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

config = GPTConfig(DIC_SIZE, 
                   max_seq,
                   dim_feedforward=512,
                   n_layer=32, 
                   n_head=32, 
                   n_embd=512,
                   enable_rpr=True,
                   er_len=max_seq)

# DO NOT FORGET TO ADJUST MODEL PARAMS IN GPT2RGAX module to your specs

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GPT(config)

model = nn.DataParallel(model)

model.to(device)

#=====

init_step = 0
lr = LR_DEFAULT_START
lr_stepper = LrStepTracker(d_model, SCHEDULER_WARMUP_STEPS, init_step)
eval_loss_func = nn.CrossEntropyLoss(ignore_index=DIC_SIZE)
train_loss_func = eval_loss_func

opt = Adam(model.parameters(), lr=lr, betas=(ADAM_BETA_1, ADAM_BETA_2), eps=ADAM_EPSILON)
lr_scheduler = LambdaLR(opt, lr_stepper.step)


#===

best_eval_acc        = 0.0
best_eval_acc_epoch  = -1
best_eval_loss       = float("inf")
best_eval_loss_epoch = -1
best_acc_file = '/content/gpt2_rpr_acc.pth'
best_loss_file = '/content/gpt2_rpr_loss.pth'
loss_train, loss_val, acc_val = [], [], []

for epoch in range(0, epochs):
    new_best = False
    
    loss = train(epoch+1, 
                 model, train_loader, 
                 train_loss_func, 
                 opt, 
                 lr_scheduler, 
                 num_iters=-1, 
                 save_checkpoint_steps=1000)
    
    loss_train.append(loss)
    
    eval_loss, eval_acc = eval_model(model, val_loader, eval_loss_func, num_iters=-1)
    loss_val.append(eval_loss)
    acc_val.append(eval_acc)
    
    if(eval_acc > best_eval_acc):
        best_eval_acc = eval_acc
        best_eval_acc_epoch  = epoch+1
        torch.save(model.state_dict(), best_acc_file)
        new_best = True

    if(eval_loss < best_eval_loss):
        best_eval_loss       = eval_loss
        best_eval_loss_epoch = epoch+1
        torch.save(model.state_dict(), best_loss_file)
        new_best = True
    
    if(new_best):
        print("Best eval acc epoch:", best_eval_acc_epoch)
        print("Best eval acc:", best_eval_acc)
        print("")
        print("Best eval loss epoch:", best_eval_loss_epoch)
        print("Best eval loss:", best_eval_loss)

#@title Eval funct to eval separately if needed


#=====

init_step = 0
lr = LR_DEFAULT_START
lr_stepper = LrStepTracker(d_model, SCHEDULER_WARMUP_STEPS, init_step)
eval_loss_func = nn.CrossEntropyLoss(ignore_index=DIC_SIZE)
train_loss_func = eval_loss_func

opt = Adam(model.parameters(), lr=lr, betas=(ADAM_BETA_1, ADAM_BETA_2), eps=ADAM_EPSILON)
lr_scheduler = LambdaLR(opt, lr_stepper.step)


eval_loss, eval_acc = eval_model(model, val_loader, eval_loss_func, num_iters=-1)

"""# (SAVE)"""

#@title Save the model

print('Saving the model...')
full_path_to_model_checkpoint = "/content/Piano-Hands-Trained-Model.pth" #@param {type:"string"}
torch.save(model.state_dict(), full_path_to_model_checkpoint)
print('Done!')

"""***

# (UNZIP PRE-TRAINED MODEL)
"""

# Commented out IPython magic to ensure Python compatibility.
#@title Unzip pre-trained Piano Hands Model
# %cd /content/Piano-Hands/Model

print('=' * 70)
print('Unzipping pre-trained model...Please wait...')
print('=' * 70)

!cat /content/Piano-Hands/Model/Piano_Hands_Trained_Model.zip* > Piano_Hands_Trained_Model.zip
print('=' * 70)

!unzip -j Piano_Hands_Trained_Model.zip
print('=' * 70)

print('Done! Enjoy! :)')
print('=' * 70)
# %cd /content/

"""# (LOAD/RELOAD)"""

#@title LOAD/RELOAD Piano Hands  Model
full_path_to_trained_model_checkpoint = "/content/Piano-Hands/Model/Piano_Hands_Trained_Model_13940_steps_0.3038_loss.pth" #@param {type:"string"}

print('Loading Piano Hands model...')
config = GPTConfig(132, 
                  512,
                  dim_feedforward=512,
                  n_layer=32, 
                  n_head=32, 
                  n_embd=512,
                  enable_rpr=True,
                  er_len=512)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GPT(config)

state_dict = torch.load(full_path_to_trained_model_checkpoint, map_location=device)

new_state_dict = OrderedDict()
for k, v in state_dict.items():
    name = k[7:] #remove 'module'
    new_state_dict[name] = v

model.load_state_dict(new_state_dict)

model.to(device)

model.eval()

print('Done!')

summary(model)

cos_sim = metrics.pairwise.cosine_similarity(
    model.tok_emb.weight.detach().cpu().numpy()
)
plt.figure(figsize=(8, 8))
plt.imshow(cos_sim, cmap="inferno", interpolation="none")
im_ratio = cos_sim.shape[0] / cos_sim.shape[1]
plt.colorbar(fraction=0.046 * im_ratio, pad=0.04)
plt.xlabel("Position")
plt.ylabel("Position")
plt.tight_layout()
plt.plot()
plt.savefig("/content/Piano-Hands-Tokens-Embeddings-Plot.png", bbox_inches="tight")

"""# (GENERATE)"""

#@title Load Piano MIDI
full_path_to_MIDI_file = "/content/Piano-Hands/Piano-Hands-Sample-MIDI-1.mid" #@param {type:"string"}

print('Loading MIDI file...')

score = TMIDIX.midi2ms_score(open(full_path_to_MIDI_file, 'rb').read())

events_matrix = []

itrack = 1

while itrack < len(score):
    for event in score[itrack]:         
        if event[0] == 'note' and event[3] != 9:
            events_matrix.append(event)
    itrack += 1

events_matrix.sort(key=lambda x: x[4], reverse=True)
events_matrix.sort(key=lambda x: x[1])

cho = []
chords = []
notes = []

pe = events_matrix[0]
for e in events_matrix:
  time = e[1] - pe[1]
  dur = e[2]
  ptc = e[4]
  vel = e[5]

  notes.append([time, dur, ptc, vel])

  if time == 0:
    cho.append([time, dur, ptc, vel])
  else:
    chords.append(cho)
    cho = []
    cho.append([time, dur, ptc, vel])

  pe = e

print('Done!')

#@title Generate Piano Hands Parts

#@markdown Increasing number of batches may help to improve precision

number_of_batches = 1 #@param {type:"slider", min:1, max:8, step:1}
model_temperature = 0.8 #@param {type:"slider", min:0.1, max:1, step:0.1}

print('=' * 70)
print('Piano Hands Model Generator')
print('=' * 70)

print('Generating...')

inp = [131]

out1 = []

for i in tqdm(range(len(chords))):

  inp.append(130)

  for j in range(len(chords[i])):

    inp.append(chords[i][j][2])

    out = model.generate_batches(torch.Tensor(inp[-511:]), 
                      target_seq_length=len(inp[-511:])+1,
                      num_batches=number_of_batches, 
                      temperature=model_temperature, verbose=False).tolist()

    ou = [y[-1] for y in out]

    o = max(set(ou), key = ou.count)

    out1.extend([o])

print('Done!')
print('=' * 70)

if len(notes) != 0:
    
    song = notes
    song_f = []
    time = 0
    dur = 0
    vel = 0
    pitch = 0
    channel = 0

    son = []

    song1 = []
    count = 0
    for s in song[:len(out1)]:

        if out1[count] == 128:
          channel = 1 # Left Hand Channel
        else:
          channel = 0 # Right Hand Channel

        time += s[0]
            
        dur = s[1]
        
        pitch = s[2]

        vel = s[3]
                                  
        song_f.append(['note', time, dur, channel, pitch, vel ])

        count += 1

    detailed_stats = TMIDIX.Tegridy_SONG_to_MIDI_Converter(song_f,
                                                        output_signature = 'Piano Hands',  
                                                        output_file_name = '/content/Piano-Hands-Music-Composition', 
                                                        track_name='Project Los Angeles',
                                                        list_of_MIDI_patches=[0, 0, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                        number_of_ticks_per_quarter=500)

print('=' * 70)

"""# Congrats! You did it! :)"""