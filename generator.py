import socket
import numpy as np
import os

def format_and_save(script, template, **kwargs):

    mem_constraint = "--mem=30G"
    partition = "t4v2"
    #qos = "nopreemption"
    qos = "normal"
    #qos = "deadline"
    
    kwargs['mem_constraint'] = mem_constraint
    kwargs['partition'] = partition
    kwargs['qos'] = qos

    temp = template.format(**kwargs)
    temp += "--eval-bleu-args \'{\"beam\": 5, \"max_len_a\": 1.2, \"max_len_b\": 10}\'"
    sc = open(script, 'w+')
    sc.write(temp)
    sc.close()

    #print(temp)

slurm_script_template = (
    "#!/bin/bash\n"
    "#SBATCH --time=7-00:00            # time (DD-HH:MM)\n"
    "#SBATCH --cpus-per-task=2         # CPU cores/threads\n"
    "#SBATCH --partition={partition} # define the partition to run on\n"
    "#SBATCH --qos={qos} # define the partition to run on\n"
    #"#SBATCH --account=deadline # define the partition to run on\n"
    "#SBATCH --gres=gpu:1                         # Number of GPUs (per node)\n"
    "#SBATCH --nodes=1\n"
    "#SBATCH --job-name={name}\n"
    "#SBATCH --output=/scratch/ssd001/home/iliash/code/keywordspotting_mixing_defense/TCResNet/log/slurm/flareon-%x-%A-%a.out # specify output file\n"
    "#SBATCH --error=/scratch/ssd001/home/iliash/code/keywordspotting_mixing_defense/TCResNet/log/error/flareon-%x-%A-%a.err  # specify error file\n"
    "#SBATCH {mem_constraint}\n"
    "export PATH=/pkgs/anaconda3/bin:$PATH\n"
    ". /pkgs/anaconda3/bin/activate {virt_env}\n"
    "module load python/3.8\n"
    "module load intel/mkl/2020.2\n"
    "echo \"$(uname -a)\"\n"
    "echo \"$(nvidia-smi)\"\n"
    "echo \"$(pwd)\"\n"
    "echo \"Running command\"\n"
    "echo \"$(which python)\"\n"
    "cd {exec_dir}\n"
)

msfp_set = [[2,2,2,16],[4,4,4,16],[8,8,8,16],[16,16,16,16],[32,32,32,16],[4,2,2,16],[8,4,4,16],[16,4,4,16]]
qt_set = [[4,4,4,16],[8,8,8,16],[16,16,16,16],[32,32,32,16],[32,32,32,32],[32,32,32,16],[16,8,8,16],[16,4,4,16]]

data = "/local/scratch-3/gy261/fairseq/data-bin/iwslt14.tokenized.de-en"
batch_size = 4096
max_epoch = 100
save_interval = max_epoch//10
scriptsfolder = "iwslt14_en2de_scripts"
isExist = os.path.exists(scriptsfolder)
eval_args = {"beam": 5, "max_len_a": 1.2, "max_len_b": 10}

if not isExist:
    # Create a new directory because it does not exist 
    os.makedirs(scriptsfolder)
    print(f"The new directory {scriptsfolder} is created!")

expfolder = "./"

for i in msfp_set:
    _temp = slurm_script_template[:]
    prefix = f'PYTORCH_FAIRSEQ_CACHE="{expfolder}" TORCH_HOME="{expfolder}" CUDA_VISIBLE_DEVICES=0 '

    command = prefix + f"fairseq-train {data} --arch qtransformer --share-decoder-input-output-embed --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0.0 --lr 5e-4 --lr-scheduler inverse_sqrt --warmup-updates 4000 --dropout 0.3 --weight-decay 0.0001 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 --max-tokens 4096 --eval-bleu --eval-bleu-detok moses --eval-bleu-remove-bpe --eval-bleu-print-samples --best-checkpoint-metric bleu --maximize-best-checkpoint-metric "
    command += f"--batch-size {batch_size} --save-dir ./checkpoints/msfp_{i[0]}{i[1]}{i[2]}{i[3]} --tensorboard-logdir ./dir/msfp_{i[0]}{i[1]}{i[2]}{i[3]} --max-epoch {max_epoch} --save-interval {save_interval} --quant-scheme msfp --quant-percentile 1 --quant-bitwidth [{i[0]},{i[1]},{i[2]},{i[3]}] --quant-bucketsize 16 "
    #command += f"--eval-bleu-args {eval_args} "
    _temp += command

    format_and_save(
      name = f"msfp_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      script = f"{scriptsfolder}/msfp_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      run_script = f"{scriptsfolder}/msfp_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      template = _temp,
      virt_env= "/scratch/ssd001/home/iliash/virts/lowb/",
      exec_dir= f"{expfolder}",
    )
    
    
    
for i in qt_set:
    _temp = slurm_script_template[:]
    prefix = f'PYTORCH_FAIRSEQ_CACHE="{expfolder}" TORCH_HOME="{expfolder}" CUDA_VISIBLE_DEVICES=0 '

    command = prefix + f"fairseq-train {data} --arch qtransformer --share-decoder-input-output-embed --optimizer adam --adam-betas '(0.9, 0.98)' --clip-norm 0.0 --lr 5e-4 --lr-scheduler inverse_sqrt --warmup-updates 4000 --dropout 0.3 --weight-decay 0.0001 --criterion label_smoothed_cross_entropy --label-smoothing 0.1 --max-tokens 4096 --eval-bleu --eval-bleu-detok moses --eval-bleu-remove-bpe --eval-bleu-print-samples --best-checkpoint-metric bleu --maximize-best-checkpoint-metric "
    command += f"--batch-size {batch_size} --save-dir ./checkpoints/qt_{i[0]}{i[1]}{i[2]}{i[3]} --tensorboard-logdir ./dir/qt_{i[0]}{i[1]}{i[2]}{i[3]} --max-epoch {max_epoch} --save-interval {save_interval} --quant-scheme fixed --quant-percentile 1 --quant-bitwidth [{i[0]},{i[1]},{i[2]},{i[3]}] --quant-bucketsize 16 "
    #command += f"--eval-bleu-args {{beam: 5, max_len_a: 1.2, max_len_b: 10}} "
    _temp += command

    format_and_save(
      name = f"qt_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      script = f"{scriptsfolder}/qt_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      run_script = f"{scriptsfolder}/qt_{i[0]}{i[1]}{i[2]}{i[3]}.sh",
      template = _temp,
      virt_env= "/scratch/ssd001/home/iliash/virts/lowb/",
      exec_dir= f"{expfolder}",
    )
