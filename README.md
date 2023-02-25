# Introduction

This code is used to generate flawed classical planning domains which serve as the benchmark sets for the empirical evaluation described in the paper: *Towards Automated Modeling Assistance: An Efficient Approach for Repairing Flawed Planning Domains*. The detailed procedure for how the benchmark sets are generated can be found in the Experimental Results section in the paper.

# Run the Code

You can use the following command to obtain a flawed domain:
```
python fuzzer.py --domain domain_file --rate error_rate --outDomain output_directory_1 --outOperations output_directory_2
```
The argument `--domain` specifies a domain file from which the flawed one will be obtained. The argument `--rate` specifies the error rate, which controls how many errors will be introduced randomly to the given domain (see the paper for how error rates are defined). The argument `--outDomain` specifies the path on which the flawed domain file, named domain.pddl, will be written. The last argument `--outOperations` defines the path on which a file called fuzz_ops.txt recording the error introduced will be produced.

# Generate the Benchmark Sets

The directory generator contains the code for generating the benchmark sets used for the evaluation in the paper. Note that since flawed domains are obtained by randomly introducing errors, it is hardly to generate benchmark sets that are identical to those in the paper. The exact benchmark sets used for the evaluation can be found in the data host where the structure of each generated benchmark set will also be depicted. 

As described in the paper, the evaluation was done on two benchmark sets. In one benchmark set, every generated flawed domain is paired with one planning task, and in the other one, every domain is paired with multiple tasks. Both benchmark sets were created based upon the [Fast-downward Problem Suite](https://github.com/aibasel/downward-benchmarks). 

The following command generates the benchmark set where one flawed domain is paired with one planning task:
```
python generator.py --single --benchmarks path_to_downward_benchmarks --fuzzer path_to_the_fuzzer --rates error_rate_1 error_rate_2 ... error_rate_n --out output_directory
```
The argument `--single` indicates the type of benchmark set that will be generated. `--benchmarks` specifies the path to the Fast-downward Problem Suite. `--fuzzer` specifies the path to the script fuzzer.py. If this argument is not given, the generator assumes that fuzzer.py is in the parent directory. `--rates` indicates that flawed domains with the given error rates will be generated. `--out` specifies the output directory of the generated benchmark sets. 

The benchmark set where each flawed domain is paired with multiple planning tasks can be generated by simply replaced the argument `--single` in the above command with `--multiple`. 

Further, you could also call the [Fast-downward](https://www.fast-downward.org/) planner to find a solution to each planning task by providing the argument `--solve` and giving the argument `--downward` the path to the planner. 