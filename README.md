# Machine Translation Final Project - Curriculum training and it's effects

This is the code behind the paper:

Run the code please use the enviroment that Phillip Koehn has provided in his course.

Please download the europarl corpus that we have extracted to a txt file from here before you try to run this:

https://1drv.ms/u/s!Am4Ha7HFtj7srIkYXQ9hyJ00ii149w?e=9IvAyF

To reproduce our results do the following:

For the batch version using curriculum training do:
```
python LSTMwithnnLstmAndBatch.py --print_every 10000 --batch_size 10 --n_epochs 50 --train_file "data/traindata.txt"  --dev_file  "data/validationdata.txt" --test_file "data/testdata.txt" --out_file "results4" --hidden_size 512 --initial_learning_rate 0.001 
```
For the batch version using non curriculum training do:
```
python LSTMwithnnLstmAndBatch.py --print_every 10000 --batch_size 10 --n_epochs 20 --train_file "data/traindataToo.txt"  --dev_file  "data/validationdataToo.txt" --test_file "data/testdataToo.txt" --out_file "results3" --hidden_size 512 --initial_learning_rate 0.001 
```
For the non  batch version using curriculum training do:
```
python LSTMwithNNlstm.py --print_every 10000 --n_epochs 10 --train_file "data/traindata.txt"  --dev_file  "data/validationdata.txt" --test_file "data/testdata.txt" --out_file "results1"
```
For the non batch version using non curriculum training do:
```
python LSTMwithNNlstm.py --print_every 10000 --n_epochs 10 --train_file "data/traindataToo.txt"  --dev_file  "data/validationdataToo.txt" --test_file "data/testdataToo.txt" --out_file "results2"
```
